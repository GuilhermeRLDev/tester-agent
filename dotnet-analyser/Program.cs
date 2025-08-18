using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

class Program
{
    public static void Main(string[] args)
    {
        if (args.Length == 0)
        {
            Console.WriteLine("Usage: CodeAnalyzer <folder>");
            return;
        }

        var folder = args[0];
        var files = Directory.GetFiles(folder, "*.cs", SearchOption.AllDirectories);

        if (files.Length == 0)
        {
            Console.WriteLine("No .cs files found.");
            return;
        }

        // 1) Parse all trees and build ONE compilation across the whole codebase
        var trees = files.Select(f => CSharpSyntaxTree.ParseText(File.ReadAllText(f), path: f)).ToList();

        // Basic framework references (add more if your code needs them)
        var references = new List<MetadataReference>
        {
            MetadataReference.CreateFromFile(typeof(object).Assembly.Location),         // mscorlib/System.Private.CoreLib
            MetadataReference.CreateFromFile(typeof(Console).Assembly.Location),        // System.Console
            MetadataReference.CreateFromFile(typeof(Enumerable).Assembly.Location)      // System.Linq
        };

        var compilation = CSharpCompilation.Create(
            assemblyName: "Analysis",
            syntaxTrees: trees,
            references: references,
            options: new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary));

        // 2) Precompute all class symbols once (used for implementation lookups)
        var allClassSymbols = trees
            .SelectMany(t => t.GetRoot().DescendantNodes().OfType<ClassDeclarationSyntax>()
                .Select(cd => compilation.GetSemanticModel(t).GetDeclaredSymbol(cd)))
            .OfType<INamedTypeSymbol>()
            .ToList();

        var outputs = new List<object>();

        foreach (var tree in trees)
        {
            var model = compilation.GetSemanticModel(tree);
            var root = tree.GetRoot();

            foreach (var classNode in root.DescendantNodes().OfType<ClassDeclarationSyntax>())
            {
                var classSymbol = model.GetDeclaredSymbol(classNode) as INamedTypeSymbol;
                var @namespace = classSymbol?.ContainingNamespace?.ToDisplayString() ?? "";
                var className = classSymbol?.ToDisplayString() ?? classNode.Identifier.Text;

                // Gather fields (name + TypeSymbol)
                var fieldsInClass = classNode.Members
                    .OfType<FieldDeclarationSyntax>()
                    .SelectMany(f => f.Declaration.Variables.Select(v =>
                    {
                        var typeInfo = model.GetTypeInfo(f.Declaration.Type);
                        var typeSymbol = typeInfo.Type as INamedTypeSymbol;
                        return new
                        {
                            Name = v.Identifier.Text,
                            TypeSymbol = typeSymbol,
                            TypeName = typeSymbol?.ToDisplayString() ?? f.Declaration.Type.ToString()
                        };
                    }))
                    .ToList();

                var methodsObj = new Dictionary<string, object>();

                // Methods (block-bodied and expression-bodied)
                var methods = classNode.Members.OfType<MethodDeclarationSyntax>();
                foreach (var method in methods)
                {
                    var methodName = method.Identifier.Text;

                    // Body node used for semantic walking
                    SyntaxNode bodyNode = (SyntaxNode)method.Body ?? (SyntaxNode)method.ExpressionBody?.Expression;
                    if (bodyNode == null) continue;

                    // METHOD CALLS: resolve to ContainingType.Method
                    var calls = bodyNode.DescendantNodes()
                        .OfType<InvocationExpressionSyntax>()
                        .Select(inv =>
                        {
                            var sym = model.GetSymbolInfo(inv).Symbol as IMethodSymbol;
                            return sym != null ? $"{sym.ContainingType.ToDisplayString()}.{sym.Name}" : null;
                        })
                        .Where(s => s != null)
                        .Distinct()
                        .ToList();

                    // FIELDS USED: identifiers that resolve to fields
                    var fieldsUsed = bodyNode.DescendantNodes()
                        .OfType<IdentifierNameSyntax>()
                        .Select(id => model.GetSymbolInfo(id).Symbol)
                        .OfType<IFieldSymbol>()
                        .Select(f => f.Name)
                        .Distinct()
                        .ToList();

                    // BRANCHES: collect if-conditions
                    var branches = bodyNode.DescendantNodes()
                        .OfType<IfStatementSyntax>()
                        .Select(ifStmt => ifStmt.Condition.ToString())
                        .ToList();

                    // SIDE EFFECTS:
                    // We consider calls like <field>.<Method>(...) as side effects on dependencies.
                    var sideEffects = new List<object>();

                    foreach (var invocation in bodyNode.DescendantNodes().OfType<InvocationExpressionSyntax>())
                    {
                        if (invocation.Expression is MemberAccessExpressionSyntax memberAccess)
                        {
                            // Resolve the "left" of the call: foo.Bar() -> resolve "foo"
                            var exprSymbolInfo = model.GetSymbolInfo(memberAccess.Expression);
                            var exprSymbol = exprSymbolInfo.Symbol;

                            if (exprSymbol is IFieldSymbol fieldSymbol)
                            {
                                var fieldType = fieldSymbol.Type as INamedTypeSymbol;
                                string invokedMethodName = memberAccess.Name.Identifier.Text;

                                // Find implementations:
                                // - If the field type is an interface, find all classes that implement it.
                                // - If the field type is a class, treat that class as the implementation.
                                var implementations = new List<string>();

                                if (fieldType != null)
                                {
                                    if (fieldType.TypeKind == TypeKind.Interface)
                                    {
                                        var impls = allClassSymbols
                                                .Where(c => c.AllInterfaces.Any(i =>
                                                    SymbolEqualityComparer.Default.Equals(i, fieldType)))
                                                .Select(c => $"{c.ToDisplayString()}.{invokedMethodName}")
                                                .Distinct()
                                                .ToList();

                                        implementations.AddRange(impls);
                                    }
                                    else if (fieldType.TypeKind == TypeKind.Class)
                                    {
                                        implementations.Add($"{fieldType.ToDisplayString()}.{invokedMethodName}");
                                    }
                                }

                                // Also store quick context for the field declaration in this class (type name etc.)
                                var declaredFieldInfo = fieldsInClass.FirstOrDefault(f => f.Name == fieldSymbol.Name);

                                sideEffects.Add(new
                                {
                                    field = fieldSymbol.Name,
                                    fieldType = declaredFieldInfo?.TypeName ?? fieldType?.ToDisplayString() ?? fieldSymbol.Type?.ToDisplayString(),
                                    interfaceType = fieldType?.TypeKind == TypeKind.Interface ? fieldType.ToDisplayString() : null,
                                    invokedMethod = invokedMethodName,
                                    implementations
                                });
                            }
                        }
                    }

                    methodsObj[methodName] = new
                    {
                        signature = method.Identifier.ToString(),
                        calls,
                        fields_used = fieldsUsed,
                        branches,
                        side_effects = sideEffects
                    };
                }

                var classObj = new Dictionary<string, object>
                {
                    ["file"] = tree.FilePath,
                    ["namespace"] = @namespace,
                    ["class"] = className,
                    ["fields"] = fieldsInClass.Select(f => new
                    {
                        name = f.Name,
                        type = f.TypeName,
                        isInterface = f.TypeSymbol?.TypeKind == TypeKind.Interface
                    }),
                    ["methods"] = methodsObj
                };

                outputs.Add(classObj);
            }
        }

        var jsonOptions = new JsonSerializerOptions
        {
            WriteIndented = true,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
        };

        string json = JsonSerializer.Serialize(outputs, jsonOptions);
        Console.WriteLine(json);

        // Write to file next to the analyzed folder (adjust as desired)
        var outDir = Path.Combine(folder, "analysis");
        Directory.CreateDirectory(outDir);
        var outPath = Path.Combine(outDir, "analysis_output.json");
        File.WriteAllText(outPath, json);

        Console.WriteLine($"Analysis complete. Output written to {outPath}");
    }
}