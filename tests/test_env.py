
import os
from pathlib import Path
from unittest import mock

from plane_mcp.__main__ import main

def test_env_file_loading(tmp_path):
    """
    Test that the .env file is loaded correctly.
    
    We simulate this by:
    1. Creating a dummy .env file in a temporary directory.
    2. Mocking `pathlib.Path` or the logic in `__main__.py` regarding path resolution 
       to point to our temporary directory.
    3. Checking if os.environ is updated.
    
    However, since `__main__.py` uses `Path(__file__).parent`, we might need to rely on
    integration style testing or careful mocking.
    
    A simpler approach for this specific test, given the simple logic:
    We can create a `.env` in the actual project root for the test duration? No, that's messy.
    
    Let's use `mock.patch` to override the path calculation in `plane_mcp.__main__`.
    """
    
    # Create a dummy .env file
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_VAR_LOADING=loaded_successful")
    
    # We want to mock:
    # current_dir = Path(__file__).parent
    # project_root = current_dir.parent
    # env_path = project_root / ".env"
    
    # If we patch `plane_mcp.__main__.Path`, we can control the returned path.
    # But `Path(__file__)` is called.
    
    with mock.patch("plane_mcp.__main__.load_dotenv") as mock_load_dotenv:
        # We also need to prevent the actual server from starting, so we mock uvicorn.run
        # or main execution flow.
        
        # main() calls load_dotenv, then looks at sys.argv, etc.
        # We just want to verifying load_dotenv is called with the right path.
        
        # We need to mock sys.argv to avoid errors or unintended behavior
        with mock.patch("sys.argv", ["plane-mcp-server"]):
             # We also need to mock uvicorn or the ServerMode logic to verify it acts as expected
             # actually main() creates a server and runs it.
             # We should probably mock `mcp.server.stdio.stdio_server` etc.
             
             # Let's just mock the `load_dotenv` call and `Path`.
             # Actually, the logic is:
             # current_dir = Path(__file__).parent
             # project_root = current_dir.parent
             # env_path = project_root / ".env"
             
             # If we run `main()`, it will execute that logic.
             # We can check `mock_load_dotenv.call_args`.
             
             # Validation: The original code uses `Path(__file__)`. 
             # We want to ensure it calculates the path relative to the installed package location
             # or source location.
             
             # Let's NOT mock Path, but checking if `load_dotenv` is called with the expected path
             # based on where `plane_mcp/__main__.py` actually lives on disk.
             
             # But we can't change the actual .env file on disk safely. 
             # So we can just verify it calls `load_dotenv` with the `.../local-plane-mcp/.env`.
             
             target_env_path = Path("plane_mcp/__main__.py").resolve().parent.parent / ".env"
             
             # Mocking everything else to exit early
             with mock.patch("plane_mcp.__main__.ServerMode"), \
                  mock.patch("plane_mcp.__main__.Server"), \
                  mock.patch("plane_mcp.__main__.stdio_server"), \
                  mock.patch("plane_mcp.__main__.sse_server"):
                 
                 main()
                 
                 mock_load_dotenv.assert_called_once()
                 # We can check the path argument if we want, but it might be strict.
                 call_args = mock_load_dotenv.call_args
                 # call_args.kwargs['dotenv_path'] or call_args[0]
                 
                 # Verify it called it with a path named .env
                 assert call_args.kwargs['dotenv_path'].name == ".env"
                 # And it's in the parent of the parent of __main__
                 expected_parent = Path("plane_mcp/__main__.py").resolve().parent.parent
                 assert call_args.kwargs['dotenv_path'].parent == expected_parent

def test_env_loading_integration(tmp_path):
    """
    A more direct test: modify os.environ via load_dotenv directly to ensure the library works.
    This just tests python-dotenv integration, not the main logic.
    """
    d = tmp_path / ".env"
    d.write_text("FOO=BAR")
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=d)
    assert os.environ.get("FOO") == "BAR"
