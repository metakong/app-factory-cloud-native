# Use an official lightweight nginx image.
FROM nginx:alpine

# Set working directory.
WORKDIR /usr/share/nginx/html

# Remove default assets.
RUN rm -rf ./*

# Copy static assets.
COPY ./ /usr/share/nginx/html/

# Expose port 80.
EXPOSE 80