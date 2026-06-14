module.exports = {
  apps: [
    {
      name: "pulsebnb-indexer",
      script: "indexer.py",
      interpreter: "/home/vps/pulsebnb/venv/bin/python",
      cwd: "/home/vps/pulsebnb",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      out_file: "/home/vps/pulsebnb/logs/indexer-out.log",
      error_file: "/home/vps/pulsebnb/logs/indexer-err.log",
    },
    {
      name: "pulsebnb-api",
      script: "/home/vps/pulsebnb/start-api.sh",
      interpreter: "bash",
      cwd: "/home/vps/pulsebnb",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      out_file: "/home/vps/pulsebnb/logs/api-out.log",
      error_file: "/home/vps/pulsebnb/logs/api-err.log",
    },
  ],
};
