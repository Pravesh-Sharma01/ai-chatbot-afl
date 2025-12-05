# Use an official node runtime as a parent image
FROM node:20-alpine

# Set the working directory
WORKDIR /app

# Copy the package.json and package-lock.json files to the working directory
COPY package*.json ./


# Declare ARGs before ENV
ARG BACKEND_DOMAIN_FIBER
ARG BACKEND_DOMAIN_MOTOR
ARG BACKEND_DOMAIN_HR
ARG BACKEND_DOMAIN_CLAIM

# Export them to environment variables so they are accessible in the build process
ENV BACKEND_DOMAIN_FIBER=$BACKEND_DOMAIN_FIBER
ENV BACKEND_DOMAIN_MOTOR=$BACKEND_DOMAIN_MOTOR
ENV BACKEND_DOMAIN_HR=$BACKEND_DOMAIN_HR
ENV BACKEND_DOMAIN_CLAIM=$BACKEND_DOMAIN_CLAIM

# Install the dependencies
RUN npm install

# Copy the rest of the application code to the working directory
COPY . .

# Build the Next.js app
RUN npm run build

# Expose the port
EXPOSE 3000

# Start the app
CMD ["npm", "run", "start"]
