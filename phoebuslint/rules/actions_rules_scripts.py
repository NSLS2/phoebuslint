# TODO: Fix import when phoebusgen is updated


# class ScriptPathDoesNotExist(LintRule[HasActionsRulesAndScripts]):
#     """Rule that checks if a widget with scripts references a non-existent script file."""

#     rule_code = "ARS1001"
#     description = "Configured script references a non-existent file."

#     @classmethod
#     def check(cls, element: HasActionsRulesAndScripts) -> bool:
#         for script in element.scripts:
#             if script.file is not None and not Path(script.file).is_file():
#                 return True
#         return False

# class IncorrectScriptFileExtension(LintRule[HasActionsRulesAndScripts]):
#     """Rule that checks if a widget with scripts references a script file with incorrect extension."""

#     rule_code = "ARS1002"
#     description = "Configured script references a file with incorrect extension."

#     @classmethod
#     def check(cls, element: HasActionsRulesAndScripts) -> bool:
#         for script in element.scripts:
#             if script.file is not None and not Path(script.file).suffix in [".py", ".js"]:
#                 return True
#         return False


# class EmptyScriptFilePath(LintRule[HasActionsRulesAndScripts]):
#     """Rule that checks if a widget with scripts has an empty script file path."""

#     rule_code = "ARS1003"
#     description = "Configured script has an empty file path."

#     @classmethod
#     def check(cls, element: HasActionsRulesAndScripts) -> bool:
#         for script in element.scripts:
#             if script.file is None or script.file.strip() == "":
#                 return True
#         return False

# class EmptyScriptContents(LintRule[HasActionsRulesAndScripts]):
#     """Rule that checks if a widget with scripts has empty script contents."""

#     rule_code = "ARS1004"
#     description = "Configured script has empty contents."

#     @classmethod
#     def check(cls, element: HasActionsRulesAndScripts) -> bool:
#         for script in element.scripts:
#             if isinstance(script, EmbeddedScript):
#                 if script.
#             if script.contents is None or script.contents.strip() == "":
#                 return True
#         return False
