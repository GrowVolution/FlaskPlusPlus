import typer


def help_message():
    typer.echo(
        "Usage: \n\t" + typer.style("fpp [args]", bold=True) + "\n"
        "\t" + typer.style("fpp [command] [args]", bold=True) + "\n"
        "\t" + typer.style("fpp [subcli] [command] [args]", bold=True) + "\n\n"
                                                                         
        "Arguments:\n\t-v, --version\t   - Show the current version of Flask++.\n"
        "\t-h, --help\t   - Show this help message.\n\n"
                                                                         
        "Commands:\n\tinit\t\t   - Initializes Flask++ (running in the current working directory).\n"
        "\tsetup\t\t   - Starts the Flask++ app setup tool. (Can be run multiple times.)\n"
        "\trun\t\t   - The Flask++ native app control. (Using uvicorn.)\n\n"
                                                                         
        "Sub-CLIs:\n\tmodules\t\t   - Manages the modules of Flask++ apps.\n"
        "\tregistry\t   - Manages the app service registry for you. (Requires admin privileges.)\n"
        "\tnode\t\t   - Allows you to run node commands with the standalone node cli. (" + typer.style("fpp node [npm/npx] [args]", bold=True) + ")\n"
        "\ttailwind\t   - Allows you to use the natively integrated tailwind cli.\n"
        "\t" + typer.style("To use node and tailwind, you need to run `", fg=typer.colors.MAGENTA)
        + typer.style("fpp init --skip-defaults --skip-babel", bold=True, fg=typer.colors.MAGENTA)
        + typer.style("` at least once.", fg=typer.colors.MAGENTA) + "\n\n\n" +

        typer.style("fpp init [args]", bold=True) + "\n"
        "\t--skip-defaults\t   - Skip creating the default Flask++ project structure.\n"
        "\t--skip-babel\t   - Skip extracting the fallback messages.\n"
        "\t--skip-tailwind\t   - Skip downloading the standalone Tailwind CLI.\n"
        "\t--skip-node\t   - Skip downloading and installing the standalone Node.js bundle.\n"
        "\t--skip-vite\t   - Skip setting up the integrated frontend engine (Vite).\n\n" +

        typer.style("fpp run [args]", bold=True) + "\n"
        "\t-i, --interactive  - Starts all your apps in interactive mode and lets you manage them.\n"
        "\t-a, --app\t   - Specify the name of a specific app, if you don't want to run interactive.\n"
        "\t-p, --port\t   - Specify the port on which your app should listen. (Default is 5000.)\n"
        "\t-d, --debug\t   - Run your app in debug mode, to get more detailed tracebacks and log debug messages. (Default is False.)\n"
        "\t\t\t     If FRONTEND_ENGINE is enabled, vite will run in dev mode. Every module runs its own dev server.\n\n\n" +

        typer.style("fpp modules [command] [args]", bold=True) + "\n"
        "\tinstall\t\t   - Install a specified Flask++ module.\n"
        "\tcreate\t\t   - Automatically create a new module to make things easier.\n\n" +

        typer.style("fpp modules install [id] [args]", bold=True) + "\n"
        "\tid\t\t   - The id of the module to install.\n"
        "\t-s, --src\t   - Specify the uri of a source directory or git remote repository to install.\n"
        "\t" + typer.style(
            "If you only specify the id, the module will be installed from our hub. (Coming soon.)",
            fg=typer.colors.MAGENTA
        ) + "\n\n" +

        typer.style("fpp modules create [name]", bold=True) + "\n"
        "\tname\t\t   - The name of the module you want to create.\n\n\n" +

        typer.style("fpp registry [command] [args]", bold=True) + "\n"
        "\tregister\t   - Register an app as a system service. (Executed when system boots up.)\n"
        "\tremove\t\t   - Remove your app from system services.\n"
        "\tstart\t\t   - Start your apps system service.\n"
        "\tstop\t\t   - Stop your apps system service.\n\n" +

        typer.style("fpp registry register [args]", bold=True) + "\n"
        "\t-a, --app\t   - The name of your app, which you want to register as a service.\n"
        "\t-p, --port\t   - The port on which your apps service should run. (Default is 5000.)\n"
        "\t-d, --debug\t   - If your service should run in debug mode.\n\n" +

        typer.style("fpp registry [remove/start/stop] [name]", bold=True) + "\n"
        "\tname\t\t   - The name of the app (which - of course - also is the service name)."
    )
