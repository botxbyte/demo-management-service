# pylint_plugins/exception_rules_checker.py
import astroid
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter


class ExceptionAndKeywordChecker(BaseChecker):
    """Custom Pylint checker enforcing FastAPI exception conventions and keyword-only args."""

    name = "exception-keyword-checker"
    priority = -1
    msgs = {
        # Exception inheritance and naming rules
        "E9920": (
            "Exception class '%s' must inherit from BaseAppException",
            "exception-must-inherit-baseappexception",
            "All exceptions must inherit from BaseAppException (except BaseAppException itself).",
        ),
        "E9921": (
            "Exception class '%s' must end with 'Exception'",
            "exception-name-must-end-with-exception",
            "All exception classes must end with 'Exception'.",
        ),
        "E9922": (
            "BaseAppException must be in 'app/exception/baseapp_exception.py'",
            "baseappexception-location-invalid",
            "BaseAppException should be located in app/exception/baseapp_exception.py.",
        ),
        "E9923": (
            "Exception file '%s' must only import from baseapp_exception.py",
            "exception-import-violation",
            "Exception files should only import BaseAppException from baseapp_exception.py.",
        ),

        # Status code rules
        "E9924": (
            "Status code must use FastAPI status constants, not hardcoded values",
            "no-hardcoded-status-codes",
            "Use 'from fastapi import status' instead of hardcoded status codes.",
        ),
        "E9925": (
            "HTTPException subclass must use 'detail=detail' in super().__init__()",
            "http-exception-use-detail",
            "Classes inheriting from HTTPException should always pass detail=detail.",
        ),
        "E9926": (
            "Non-HTTPException subclass must use 'message=message' in super().__init__()",
            "non-http-exception-use-message",
            "Classes not inheriting from HTTPException should always pass message=message.",
        ),
    }

    # ---------------- Utility helpers ----------------
    def _is_exception_file(self, node: astroid.NodeNG) -> bool:
        """Return True if file looks like an exception module."""
        filename = node.root().file or ""
        return filename.endswith("_exception.py")

    def _is_baseapp_exception_file(self, node: astroid.NodeNG) -> bool:
        """Return True if file is the baseapp_exception.py file."""
        filename = node.root().file or ""
        return filename.endswith("baseapp_exception.py")

    def _inherits_from_httpexception(self, node: astroid.ClassDef) -> bool:
        """Check if a class inherits from HTTPException (directly or through BaseAppException)."""
        try:
            # Check direct bases
            for base in node.bases:
                base_name = base.as_string()
                if "HTTPException" in base_name:
                    return True
                
                # Check if inheriting from BaseAppException, which inherits from HTTPException
                if "BaseAppException" in base_name:
                    return True
            
            # Try to infer ancestors
            for ancestor in node.ancestors():
                if ancestor.name in ("HTTPException", "BaseAppException"):
                    return True
        except (astroid.InferenceError, AttributeError, TypeError):
            pass
        
        return False

    # ---------------- Checks ----------------
    def _check_super_init_call(self, node: astroid.ClassDef):
        """Check that super().__init__() uses correct keyword argument."""
        # Skip BaseAppException itself
        if node.name == "BaseAppException":
            return
        
        inherits_httpexception = self._inherits_from_httpexception(node)

        for func_node in node.nodes_of_class(astroid.FunctionDef):
            if func_node.name != "__init__":
                continue

            for call_node in func_node.nodes_of_class(astroid.Call):
                # Check if this is a super().__init__() call
                if isinstance(call_node.func, astroid.Attribute) and call_node.func.attrname == "__init__":
                    # Check if it's calling super()
                    if isinstance(call_node.func.expr, astroid.Call):
                        func_name = getattr(call_node.func.expr.func, 'name', None)
                        if func_name == 'super':
                            self._validate_super_init_keywords(call_node, inherits_httpexception)

    def _validate_super_init_keywords(self, call_node: astroid.Call, inherits_httpexception: bool):
        """Validate the keyword arguments in super().__init__() call."""
        has_detail = False
        has_message = False
        
        for keyword in call_node.keywords:
            if keyword.arg == "detail":
                has_detail = True
                # Check if the value being passed is 'message' variable
                if inherits_httpexception:
                    # Should use detail=message (passing message variable to detail parameter)
                    if isinstance(keyword.value, astroid.Name) and keyword.value.name != "message":
                        self.add_message("http-exception-use-detail", node=call_node)
                else:
                    # Non-HTTPException should not use detail at all
                    self.add_message("non-http-exception-use-message", node=call_node)
            
            elif keyword.arg == "message":
                has_message = True
                if inherits_httpexception:
                    # HTTPException subclass should use detail=message, not message=message
                    self.add_message("http-exception-use-detail", node=call_node)
                else:
                    # Should use message=message (passing message variable to message parameter)
                    if isinstance(keyword.value, astroid.Name) and keyword.value.name != "message":
                        self.add_message("non-http-exception-use-message", node=call_node)

    # ---------------- Visitor overrides ----------------
    def visit_module(self, node: astroid.Module):
        """Module-level checks for exception files."""
        if not (self._is_exception_file(node) or self._is_baseapp_exception_file(node)):
            return

        # BaseAppException location
        if self._is_baseapp_exception_file(node):
            normalized_path = (node.file or "").replace("\\", "/")
            if not normalized_path.endswith("app/exception/baseapp_exception.py"):
                for class_node in node.nodes_of_class(astroid.ClassDef):
                    if class_node.name == "BaseAppException":
                        self.add_message("baseappexception-location-invalid", node=class_node)

        # Imports check
        if self._is_exception_file(node) and not self._is_baseapp_exception_file(node):
            for import_node in node.nodes_of_class(astroid.ImportFrom):
                if import_node.modname and "exception" in import_node.modname:
                    if not import_node.modname.endswith("baseapp_exception"):
                        self.add_message(
                            "exception-import-violation",
                            node=import_node,
                            args=(import_node.modname,),
                        )

    def visit_classdef(self, node: astroid.ClassDef):
        """Class-level checks for exception classes."""
        if not (self._is_exception_file(node) or self._is_baseapp_exception_file(node)):
            return

        # Naming convention
        if not node.name.endswith("Exception"):
            self.add_message("exception-name-must-end-with-exception", node=node, args=(node.name,))

        # Must inherit from BaseAppException (except BaseAppException itself)
        if node.name != "BaseAppException":
            base_names = [b.as_string() for b in node.bases]
            if "BaseAppException" not in "".join(base_names) and not self._is_baseapp_exception_file(node):
                self.add_message("exception-must-inherit-baseappexception", node=node, args=(node.name,))

        # Check super().__init__() calls
        self._check_super_init_call(node)

    def visit_assign(self, node: astroid.Assign):
        """Check for hardcoded HTTP status codes in exception files."""
        if not (self._is_exception_file(node) or self._is_baseapp_exception_file(node)):
            return

        if isinstance(node.value, astroid.Const) and isinstance(node.value.value, int):
            if 100 <= node.value.value <= 599:
                self.add_message("no-hardcoded-status-codes", node=node)


def register(linter: PyLinter):
    """Register the checker with pylint."""
    linter.register_checker(ExceptionAndKeywordChecker(linter))