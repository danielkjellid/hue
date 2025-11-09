"""
Tailwind CSS integration for hue components.

This module provides functionality to:
- Scan hue components for Tailwind classes
- Compile CSS using tailwindcss CLI (v4)
- Combine component classes with user-defined classes from the project
"""

import ast
import importlib
import inspect
import re
import subprocess
from pathlib import Path


class TailwindManager:
    """
    Manages Tailwind CSS compilation for hue components.

    Scans Python component files for Tailwind classes and compiles them
    along with user-defined classes into a single CSS file.
    """

    def __init__(
        self,
        output_path: str | Path,
        input_path: str | Path | None = None,
        content_paths: list[str | Path] | None = None,
        component_modules: list[str] | None = None,
        project_root: str | Path | None = None,
    ) -> None:
        """
        Initialize the Tailwind manager.

        Args:
            output_path: Path where the compiled CSS file will be written
            input_path: Path to the input CSS file (if None, uses hue's default)
            content_paths: Additional paths to scan for Tailwind classes
                (e.g., user templates, HTML files)
            component_modules: List of module paths to scan for hue components
                (e.g., ['hue.ui', 'myapp.components'])
            project_root: Root directory of the project using hue (for scanning)
        """
        self.output_path = Path(output_path)

        # Default to hue's input CSS file if not provided
        if input_path is None:
            # Try to find hue's static/styles/tailwind.input.css
            try:
                import hue

                hue_path = Path(inspect.getfile(hue)).parent
                default_input = hue_path / "static" / "styles" / "tailwind.input.css"
                if default_input.exists():
                    self.input_path = default_input
                else:
                    # Fallback to output directory
                    self.input_path = self.output_path.parent / "input.css"
            except Exception:
                # Fallback to output directory
                self.input_path = self.output_path.parent / "input.css"
        else:
            self.input_path = Path(input_path)

        self.content_paths = [Path(p) for p in (content_paths or [])]
        self.component_modules = component_modules or []
        self.project_root = Path(project_root) if project_root else None

    def extract_classes_from_string(self, text: str) -> set[str]:
        """
        Extract Tailwind classes from a string.

        Looks for class attributes in HTML-like strings and extracts
        class values that contain Tailwind classes.
        """
        classes = set()

        # Pattern to match class="..." or class_="..." attributes
        class_pattern = r'class(?:es)?(?:_)?=["\']([^"\']+)["\']'
        matches = re.findall(class_pattern, text, re.IGNORECASE)

        for match in matches:
            # Split by whitespace and add each class
            for cls in match.split():
                if cls.strip():
                    classes.add(cls.strip())

        return classes

    def extract_classes_from_ast(self, node: ast.AST) -> set[str]:
        """
        Extract Tailwind classes from a Python AST node.

        Recursively searches for string literals that might contain
        Tailwind classes, particularly in class_ attributes.
        """
        classes = set()

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            # Check if this string looks like it contains classes
            extracted = self.extract_classes_from_string(node.value)
            classes.update(extracted)

        elif isinstance(node, ast.Str):  # Python < 3.8 compatibility
            extracted = self.extract_classes_from_string(node.s)
            classes.update(extracted)

        # Recursively visit child nodes
        for child in ast.iter_child_nodes(node):
            classes.update(self.extract_classes_from_ast(child))

        return classes

    def scan_component_file(self, file_path: Path) -> set[str]:
        """
        Scan a Python file for Tailwind classes.

        Parses the file as AST and extracts classes from string literals,
        particularly focusing on class_ attributes in component definitions.
        """
        if not file_path.exists():
            return set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))
            return self.extract_classes_from_ast(tree)
        except Exception:
            # If parsing fails, fall back to regex-based extraction
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
                return self.extract_classes_from_string(source)
            except Exception:
                return set()

    def scan_component_module(self, module_path: str) -> set[str]:
        """
        Scan a Python module for Tailwind classes.

        Attempts to import the module and scan all Python files
        in the module's package.
        """
        classes = set()

        try:
            module = importlib.import_module(module_path)
            module_file = inspect.getfile(module)
            module_path_obj = Path(module_file)

            # If it's a package, scan all Python files in it
            if module_path_obj.is_file() and module_path_obj.suffix == ".py":
                # Single module file
                classes.update(self.scan_component_file(module_path_obj))
            elif (
                module_path_obj.is_dir()
                or (module_path_obj.parent / "__init__.py").exists()
            ):
                # Package - scan all Python files
                package_dir = (
                    module_path_obj.parent
                    if module_path_obj.suffix == ".py"
                    else module_path_obj
                )
                for py_file in package_dir.rglob("*.py"):
                    classes.update(self.scan_component_file(py_file))
        except Exception:
            # If import fails, try to find the module path directly
            pass

        return classes

    def scan_content_paths(self) -> set[str]:
        """
        Scan content paths (HTML templates, etc.) for Tailwind classes.

        Scans HTML, HTM, and other template files for class attributes.
        """
        classes = set()

        for content_path in self.content_paths:
            if not content_path.exists():
                continue

            # Scan HTML-like files
            for ext in ["*.html", "*.htm", "*.jinja", "*.jinja2"]:
                for file_path in content_path.rglob(ext):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        classes.update(self.extract_classes_from_string(content))
                    except Exception:
                        continue

        return classes

    def collect_all_classes(self) -> set[str]:
        """
        Collect all Tailwind classes from components and content paths.
        """
        all_classes = set()

        # Scan component modules
        for module_path in self.component_modules:
            all_classes.update(self.scan_component_module(module_path))

        # Scan content paths
        all_classes.update(self.scan_content_paths())

        return all_classes

    def create_tailwind_config_content(self, classes: set[str]) -> str:
        """
        Create a Tailwind config content string that safelists the found classes.

        Note: This is a fallback. pytailwindcss should handle content scanning,
        but we can use this to ensure all classes are included.
        """
        # For now, we'll rely on pytailwindcss's content scanning
        # This method can be extended if needed for safelisting
        return ""

    def ensure_input_css(self) -> None:
        """
        Ensure the input CSS file exists with Tailwind directives.
        """
        if not self.input_path.exists():
            self.input_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.input_path, "w", encoding="utf-8") as f:
                f.write('@import "tailwindcss";\n')

    def get_project_content_paths(self) -> list[Path]:
        """
        Get content paths from the project root that imports hue.

        Scans the project root for common template and source directories.
        """
        paths = []

        if self.project_root and Path(self.project_root).exists():
            project_root = Path(self.project_root)

            # Common directories to scan
            common_dirs = [
                "templates",
                "static",
                "src",
                "app",
                "apps",
                "components",
            ]

            for dir_name in common_dirs:
                dir_path = project_root / dir_name
                if dir_path.exists() and dir_path.is_dir():
                    paths.append(dir_path)

            # Also scan the project root itself for Python files
            paths.append(project_root)

        return paths

    def get_content_paths(
        self, additional_content: list[str | Path] | None = None
    ) -> list[Path]:
        """
        Get all content paths that Tailwind should scan.

        Returns a list of Path objects that Tailwind v4 will automatically scan.
        """
        paths = []

        # Add explicitly provided content paths
        paths.extend(self.content_paths)

        # Add the entire hue package by default (if available)
        try:
            import hue

            hue_path = Path(inspect.getfile(hue)).parent
            paths.append(hue_path)
        except Exception:
            # If hue package is not available, that's okay
            pass

        # Add component module paths (for additional modules beyond hue)
        for module_path in self.component_modules:
            try:
                module = importlib.import_module(module_path)
                module_file = inspect.getfile(module)
                module_path_obj = Path(module_file)
                if module_path_obj.is_file():
                    paths.append(module_path_obj.parent)
                elif (
                    module_path_obj.is_dir()
                    or (module_path_obj.parent / "__init__.py").exists()
                ):
                    package_dir = (
                        module_path_obj.parent
                        if module_path_obj.suffix == ".py"
                        else module_path_obj
                    )
                    paths.append(package_dir)
            except Exception:
                pass

        # Add project root paths (user's project)
        paths.extend(self.get_project_content_paths())

        # Add additional content
        if additional_content:
            for path in additional_content:
                path_obj = Path(path)
                if path_obj.exists():
                    paths.append(path_obj)

        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in paths:
            path_str = str(path.resolve())
            if path_str not in seen:
                seen.add(path_str)
                unique_paths.append(path)

        return unique_paths

    def compile_css(
        self,
        additional_content: list[str | Path] | None = None,
        minify: bool = True,
    ) -> Path:
        """
        Compile Tailwind CSS using tailwindcss CLI (v4).

        Args:
            additional_content: Additional file paths to include in content scanning
            minify: Whether to minify the output CSS

        Returns:
            Path to the compiled CSS file
        """
        # Ensure input CSS exists
        self.ensure_input_css()

        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get content paths - Tailwind v4 will automatically scan these
        content_paths = self.get_content_paths(additional_content)

        # Build tailwindcss command
        # Try 'uv run tailwindcss' first, then fall back to 'tailwindcss'
        cmd = None
        for cmd_name in ["uv", "tailwindcss"]:
            try:
                if cmd_name == "uv":
                    # Try uv run tailwindcss
                    test_cmd = ["uv", "run", "tailwindcss", "--help"]
                else:
                    test_cmd = ["tailwindcss", "--help"]

                result = subprocess.run(
                    test_cmd,
                    capture_output=True,
                    check=False,
                )
                if result.returncode == 0 or "tailwindcss" in str(result.stderr):
                    if cmd_name == "uv":
                        cmd = ["uv", "run", "tailwindcss"]
                    else:
                        cmd = ["tailwindcss"]
                    break
            except FileNotFoundError:
                continue

        if cmd is None:
            raise RuntimeError(
                "tailwindcss not found. Please install it with: "
                "uv tool install tailwindcss or npm install -g tailwindcss"
            )

        # Add input and output paths
        cmd.extend(["-i", str(self.input_path), "-o", str(self.output_path)])

        if minify:
            cmd.append("--minify")

        # Set content paths via environment variable or working directory
        # Tailwind v4 automatically scans from the input file's directory
        # and parent directories, so we need to ensure the working directory
        # is set appropriately, or use the --content flag if available

        # For Tailwind v4, content scanning is automatic based on the project structure
        # The content paths are used to set the working directory context
        # We'll set the working directory to the project root if available
        cwd = None
        if self.project_root and Path(self.project_root).exists():
            cwd = Path(self.project_root)
        elif content_paths:
            # Use the first content path's parent as working directory
            cwd = (
                content_paths[0].parent
                if content_paths[0].is_file()
                else content_paths[0]
            )

        # Run tailwindcss
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                cwd=cwd,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to compile Tailwind CSS: {e.stderr or e.stdout}"
            ) from e
        except FileNotFoundError:
            raise RuntimeError(
                "tailwindcss not found. Please install it with: "
                "uv tool install tailwindcss or npm install -g tailwindcss"
            )

        return self.output_path

    def get_css_path(self) -> Path:
        """
        Get the path to the compiled CSS file.

        This can be used to check if compilation is needed or to
        get the path for template inclusion.
        """
        return self.output_path
