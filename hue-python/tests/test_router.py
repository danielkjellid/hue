import inspect

from src.hue.router import Router


def test_router_initialization():
    """Test that router initializes with empty routes."""
    router = Router()
    assert router.get_routes() == []


def test_register_get_route():
    """Test registering a GET route."""
    router = Router()

    @router.get("/")
    def index():
        return "index"

    routes = router.get_routes()
    assert len(routes) == 1
    route = routes[0]
    assert route.method == "GET"
    assert route.path == ""
    assert route.handler == index
    assert route.is_ajax is False
    assert route.path_params == []


def test_register_ajax_get_route():
    """Test registering an AJAX GET route."""
    router = Router()

    @router.ajax_get("comments/")
    def comments():
        return "comments"

    routes = router.get_routes()
    assert len(routes) == 1
    route = routes[0]
    assert route.method == "GET"
    assert route.path == "comments/"
    assert route.handler == comments
    assert route.is_ajax is True


def test_register_ajax_post_route():
    """Test registering an AJAX POST route."""
    router = Router()

    @router.ajax_post("comments/")
    def create_comment():
        return "create"

    routes = router.get_routes()
    assert len(routes) == 1
    route = routes[0]
    assert route.method == "POST"
    assert route.path == "comments/"
    assert route.is_ajax is True


def test_register_multiple_http_methods():
    """Test registering routes with different HTTP methods."""
    router = Router()

    @router.ajax_get("items/")
    def get_items():
        return "get"

    @router.ajax_post("items/")
    def create_item():
        return "create"

    @router.ajax_put("items/")
    def update_item():
        return "update"

    @router.ajax_delete("items/")
    def delete_item():
        return "delete"

    @router.ajax_patch("items/")
    def patch_item():
        return "patch"

    routes = router.get_routes()
    assert len(routes) == 5
    methods = [route.method for route in routes]
    assert "GET" in methods
    assert "POST" in methods
    assert "PUT" in methods
    assert "DELETE" in methods
    assert "PATCH" in methods


def test_path_normalization_strips_leading_slash():
    """Test that leading slashes are stripped from paths."""
    router = Router()

    @router.get("/")
    def root():
        return "root"

    @router.get("/users/")
    def users():
        return "users"

    @router.get("/posts/comments/")
    def comments():
        return "comments"

    routes = router.get_routes()
    assert routes[0].path == ""
    assert routes[1].path == "users/"
    assert routes[2].path == "posts/comments/"


def test_path_with_parameters_base_router():
    """Test that base router doesn't parse parameters by default."""
    router = Router()

    @router.ajax_get("comments/<int:comment_id>/")
    def comment(comment_id):
        return f"comment {comment_id}"

    routes = router.get_routes()
    assert len(routes) == 1

    comment_route = routes[0]
    # Base router doesn't parse parameters, so path_params should be empty
    assert comment_route.path == "comments/<int:comment_id>/"
    assert comment_route.path_params == []


def test_get_routes_returns_copy():
    """Test that get_routes() returns a copy, not the original list."""
    router = Router()

    @router.get("/")
    def index():
        return "index"

    routes1 = router.get_routes()
    routes2 = router.get_routes()

    assert routes1 is not router._routes
    assert routes1 is not routes2
    assert routes1 == routes2


def test_find_route_by_method_and_path():
    """Test finding a route by method and path."""
    router = Router()

    @router.get("/")
    def index():
        return "index"

    @router.ajax_get("comments/")
    def comments():
        return "comments"

    @router.ajax_post("comments/")
    def create_comment():
        return "create"

    # Find GET route
    route = router.find_route("GET", "")
    assert route is not None
    assert route.handler == index
    assert route.is_ajax is False

    # Find AJAX GET route
    route = router.find_route("GET", "comments/", is_ajax=True)
    assert route is not None
    assert route.handler == comments
    assert route.is_ajax is True

    # Find AJAX POST route
    route = router.find_route("POST", "comments/", is_ajax=True)
    assert route is not None
    assert route.handler == create_comment


def test_find_route_case_insensitive_method():
    """Test that find_route is case-insensitive for HTTP methods."""
    router = Router()

    @router.get("/")
    def index():
        return "index"

    route1 = router.find_route("GET", "")
    route2 = router.find_route("get", "")
    route3 = router.find_route("Get", "")

    assert route1 is not None
    assert route2 is not None
    assert route3 is not None
    assert route1.handler == route2.handler == route3.handler


def test_find_route_with_trailing_slash_variations():
    """Test that find_route handles trailing slash variations."""
    router = Router()

    @router.get("users/")
    def users():
        return "users"

    # Should match with trailing slash
    route1 = router.find_route("GET", "users/")
    assert route1 is not None

    # Should match without trailing slash
    route2 = router.find_route("GET", "users")
    assert route2 is not None
    assert route2.handler == users


def test_find_route_filters_by_ajax_flag():
    """Test that find_route can filter by is_ajax flag."""
    router = Router()

    @router.get("/")
    def index():
        return "index"

    @router.ajax_get("/")
    def ajax_index():
        return "ajax_index"

    # Find non-AJAX route
    route = router.find_route("GET", "", is_ajax=False)
    assert route is not None
    assert route.handler == index
    assert route.is_ajax is False

    # Find AJAX route
    route = router.find_route("GET", "", is_ajax=True)
    assert route is not None
    assert route.handler == ajax_index
    assert route.is_ajax is True


def test_find_route_returns_none_when_not_found():
    """Test that find_route returns None when route doesn't exist."""
    router = Router()

    @router.get("/")
    def index():
        return "index"

    # Non-existent path
    route = router.find_route("GET", "nonexistent/")
    assert route is None

    # Non-existent method
    route = router.find_route("POST", "")
    assert route is None


def test_route_decorator_returns_handler():
    """Test that route decorators return the handler function."""
    router = Router()

    def my_handler():
        return "handler"

    # Decorator should return the handler
    decorated = router.get("/")(my_handler)
    assert decorated == my_handler

    decorated = router.ajax_get("comments/")(my_handler)
    assert decorated == my_handler


def test_multiple_routes_same_path_different_methods():
    """Test registering multiple routes with same path but different methods."""
    router = Router()

    @router.ajax_get("api/users/")
    def get_users():
        return "get"

    @router.ajax_post("api/users/")
    def create_user():
        return "create"

    @router.ajax_put("api/users/")
    def update_user():
        return "update"

    routes = router.get_routes()
    assert len(routes) == 3

    # All should have same path but different methods
    paths = {route.path for route in routes}
    assert paths == {"api/users/"}

    methods = {route.method for route in routes}
    assert methods == {"GET", "POST", "PUT"}


def test_route_with_no_parameters():
    """Test route with no URL parameters."""
    router = Router()

    @router.get("simple/")
    def simple():
        return "simple"

    routes = router.get_routes()
    route = routes[0]
    assert route.path_params == []


def test_async_handler_registration():
    """Test that async handlers can be registered."""
    router = Router()

    @router.get("/")
    async def async_index():
        return "async_index"

    routes = router.get_routes()
    assert len(routes) == 1
    assert routes[0].handler == async_index
    assert inspect.iscoroutinefunction(async_index)
