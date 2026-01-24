# 🧪 Flask++

Tired of setting up Flask from scratch every single time? 🤯  
With **Flask++**, you can spin up and manage multiple apps in **under two minutes**. ⚡

And most important: This is **still Flask**. You won't have to miss the feeling of developing Flask.
You've got **full control** about how much magic you would like to use and how much this framework should just feel like Flask.
Not only that: If you experience something, which doesn't feel like Flask anymore... Please feel free to raise an issue and we'll fix that for you asap. ✌🏼️

It comes with the most common Flask extensions pre-wired and ready to go.  
Configuration is dead simple – extensions can be bound or unbound with ease.  
On top of that, it features a plug-&-play style **module system**, so you can just enable or disable functionality as needed. 🎚️

---

## 💡 Getting Started
If not already done, just install Python 3.10 or higher on your system. Then install Flask++ like every other python package:

```bash
pip install flaskpp
````

After that you can simply setup your app with the Flask++ CLI:

```bash
mkdir myproject
cd myproject

fpp init

# If you want to use modules, we recommend to create / install them before the setup.
# This will make life even easier, because you won't need to add them to your app config manually.

fpp modules create [name]
fpp modules install [id] [-s/--src] path/to/module

# You can also install from remote repositories (e.g. our I18n Manager):
fpp modules install i18n_module --src https://github.com/GrowVolution/FPP_i18n_module

fpp setup

# You can run your app(s) interactively:
fpp run [-i/--interactive]
# Or straight up:
fpp run [-a/--app] myapp [-p/--port] 5000 [-d/--debug]

# For further assistance use:
fpp --help
```

The setup wizard will guide you through the configuration step by step. 🎯
Once finished, your first app will be running – in less than the time it takes to make coffee. ☕🔥

**Tip:** We recommend installing Flask++ globally. If your OS does not support installing PyPI packages outside virtual environments,
you can create a workaround like this:

```bash
sudo su
cd /opt
mkdir flaskpp
cd flaskpp

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install flaskpp

cat > cli <<EOF
#!/usr/bin/env bash
exec /opt/flaskpp/.venv/bin/python -m flaskpp "$@"
EOF
chmod +x cli
ln -s /opt/flaskpp/cli /usr/local/bin/fpp

cd ..
groupadd shared
find /home -mindepth 1 -maxdepth 1 -type d -print0 |
while IFS= read -r -d '' dir; do
    user=$(basename "$dir")
    usermod -aG shared "$user"
done
chown -R root:shared flaskpp
chmod -R 2775 flaskpp
exit

newgrp shared
```

---

## 🧩 Modules

To get started with modules, you can generate basic modules using the Flask++ CLI: `fpp modules create [module_name]`
Use as a starting point for your own modules. 😉

---

## 🌐 Proxy Example (nginx)

If you’re deploying on a server, you can bind your app to a domain via nginx:

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name myapp.example.org;

    ssl_certificate     /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        include proxy_params;   # default at /etc/nginx/

        # optional tweaks:
        # client_max_body_size 16M;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_http_version 1.1;
        # better: put these lines in /etc/nginx/upgrade_params
        # and simply use: include upgrade_params;
    }
}
```

---

## 📝 Documentation

For further information about this framework and how to use it, you may like to read our [documentation](DOCS.md). 🫶🏼

> ⚠️ Note: The documentation is intended as an architectural and reference guide, it does not provide a step-by-step tutorial.
> This is especially because Flask++ is a CLI first framework that provides a zero-code bootstrapping experience.

---

### 🌱 Let it grow

If you like this project, feel free to **fork it, open issues, or contribute ideas**.
Every improvement makes life easier for the next developer. 💚

---

### 📜 License

Released under the [MIT License](LICENSE).
Do whatever you want with it – open-source, commercial, or both. Follow your heart. 💯

---

**&copy; GrowVolution e.V. 2025 – Release the brakes! 🚀**
