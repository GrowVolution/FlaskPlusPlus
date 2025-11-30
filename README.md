# 🧪 Flask++

Tired of setting up Flask from scratch every single time? 🤯  
With **Flask++**, you can spin up and manage multiple apps in **under two minutes** ⚡.

It comes with the most common Flask extensions pre-wired and ready to go.  
Configuration is dead simple – extensions can be bound or unbound with ease.  
On top of that, it features a plug-&-play style **module system**, so you can just enable or disable functionality as needed. 🎚️

---

## 💡 Getting Started
Clone the repo and launch the setup tool:

```bash
cd /path/to/Flask++
chmod +x setup.sh
(sudo) ./setup.sh
````

On Windows:

```bat
cd \path\to\Flask++
setup.bat
```

The setup wizard will guide you through configuration step by step. 🎯
Once finished, your first app will be running – in less than the time it takes to make coffee. ☕🔥

---

## 🧩 Modules

Inside `modules/*` you’ll find an example module to get you started.
Use it as a template to quickly build your own features. 😉

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

## 🌱 Let it grow

If you like this project, feel free to **fork it, open issues, or contribute ideas**.
Every improvement makes life easier for the next developer. 💚

---

## 📜 License

Released under the [MIT License](LICENSE).
Do whatever you want with it – open-source, commercial, or both. Follow your heart. 💯

---

**GrowVolution 2025 – Release the brakes! 🚀**