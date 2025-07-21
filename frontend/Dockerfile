# Use an official lightweight nginx image as a parent image
FROM nginx:alpine

# Set the working directory to nginx's web root
WORKDIR /usr/share/nginx/html

# Remove default nginx static assets
RUN rm -rf ./*

# Copy the static assets from the a "public" directory
COPY ./ /usr/share/nginx/html/

# Expose port 80
EXPOSE 80

