FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html styles.css app.js icons.js logo.svg /usr/share/nginx/html/
COPY fonts /usr/share/nginx/html/fonts
EXPOSE 80
