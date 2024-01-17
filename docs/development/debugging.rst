.. _debugging:

----------------------
Debugging with debugpy
----------------------

If you are working with Visuals Studio Code, you might want to enabel 
**debugpy** for debugging. To do so, change DEBUGGER_DEBUGPY=1 in .env.

In VS Code choode **Reopen in Container** after installing the appropriate
VS Code extensions and put this code where you want the debugger to break:

    .. code-block:: python

    import debugpy
    debugpy.listen(("0.0.0.0", 5253))
    print("Waiting for debugger attach")
    debugpy.wait_for_client()
    debugpy.breakpoint()

Now trigger the code part, so the interpreter runs into the listen member
and you can chose **Docker Attach** in VS Code's Debug tab.