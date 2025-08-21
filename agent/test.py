import re

code = """
        @@ -32 +32 @@ namespace PSD2Authentication.Controllers
-            .Tap(result => _logger.LogInformation($"ControllerName: {nameof(ConfigurationController)} MethodName: {nameof(Get)} - 200"))
+            .Tap(result => _logger.LogInformation($"ControllerNames: {nameof(ConfigurationController)} MethodName: {nameof(Get)} - 200"))
@@ -38 +38 @@ namespace PSD2Authentication.Controllers
-            .Tap(result => _logger.LogInformation($"ControllerName: {nameof(ConfigurationController)} MethodName: {nameof(Post)} - 200"))
+            .Tap(result => _logger.LogInformation($"ControllerNames: {nameof(ConfigurationController)} MethodName: {nameof(Post)} - 200"))
@@ -41 +41,27 @@ namespace PSD2Authentication.Controllers
-    }
+
+
+        [HttpPut]
+        public async Task<ActionResult> Put(Configuration configuration)
+        {
+
+            if (configuration == null)
+            {
+                return BadRequest("Configuration cannot be null.");
+            }
+
+            if (string.IsNullOrEmpty(configuration.BankAuthResource) || string.IsNullOrEmpty(configuration.BankId))
+            {
+                return BadRequest("BankAuthResource and BankId cannot be empty.");
+            }
+
+            var result = await _configurationRepository.Insert(configuration);
+
+            if (result.IsFailure)
+            {
+                return BadRequest("Failed to insert configuration.");
+            }
+
+            return GetResponseFromResult(result); 
+        }
+    } 
+    
diff --git a/PSD2Authentication/PSD2Authentication/PSD2Authentication/Program.cs b/PSD2Authentication/PSD2Authentication/PSD2Authentication/Program.cs
old mode 100644
new mode 100755
diff --git a/PSD2Authentication/PSD2Authentication/PSD2Authentication/Startup.cs b/PSD2Authentication/PSD2Authentication/PSD2Authentication/Startup.cs
old mode 100644
new mode 100755
diff --git a/PSD2Authentication/PSD2Authentication/PSD2Authentication/obj/Debug/netcoreapp3.1/.NETCoreApp,Version=v3.1.AssemblyAttributes.cs b/PSD2Authentication/PSD2Authentication/PSD2Authentication/obj/Debug/netcoreapp3.1/.NETCoreApp,Version=v3.1.AssemblyAttributes.cs
new file mode 100644
index 0000000..1b9b2f8
--- /dev/null
"""


def after_version_from_unified_diff(diff_text: str) -> str:
    out = []
    for line in diff_text.splitlines():
        if line.startswith('diff --git') or line.startswith('index ') \
           or line.startswith('--- ') or line.startswith('+++ ') \
           or line.startswith('@@'):
            continue
        if line.startswith('+') or line.startswith(' '):
            out.append(line[1:])  # drop the first diff marker char
    return '\n'.join(out)

# Then apply a robust method regex to the cleaned code
method_pattern = re.compile(
    r'(public|private|protected|internal)\s+'      # access modifier
    r'(async\s+)?'                                 # async
    r'([\w<>\[\],\s]+)\s+'                         # return type (allow generics, arrays, spaces)
    r'(\w+)\s*'                                    # method name
    r'\(([^)]*)\)\s*'                              # parameters
    r'(?:=>|{)',                                   # body starts
    re.MULTILINE
    )


clean = after_version_from_unified_diff(code)
for m in method_pattern.finditer(clean):
    print(m.group(4))



