FROM nginx:alpine

# Copy static frontend files to Nginx html directory
COPY . /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
