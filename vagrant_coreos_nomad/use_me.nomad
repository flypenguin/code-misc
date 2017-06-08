# THIS IS WORK IN PROGRESS AND DOES NOT WORK YET.

job "redgreen" {

  # ok
  datacenters = ["dc1"]

  # required, although the docs indicate otherwise
  region = "global"

  # one per node
  type = "system"

  # required, although the docs indicate otherwise
  priority = 50

  update {
    stagger = "10s"
    max_parallel = 1
  }

  group "redgreen" {

    # with system-type jobs ... ?
    count = 1

    restart {
      attempts = 25
      interval = "5m"
      delay = "10s"
      mode = "delay"
    }

    task "redgreen" {
      driver = "docker"

      config {
        image = "flypenguin/test_server:red"
        port_map {
          # this says which port the CONTAINER listens on internally
          server = 80
        }
      }

      resources {
        cpu    = 50  # 50 MHz, minimum
        memory = 25  # 25MB
        network {
          # this allocates a dynamic host port and maps it to the one in the
          # container with the same name ("server") as above. so you can map
          # multiple ports.
          port "server" {}

          # mbits is REQUIRED
          mbits = 1
        }
      }

      # required, although the docs indicate otherwise
      logs {
        max_files     = 10
        max_file_size = 10
      }      

      # this is for consul. let's not do this :)
      # service {
      #   name = "global-redis-check"
      #   tags = ["global", "cache"]
      #   port = "db"
      #   check {
      #     name     = "alive"
      #     type     = "http"
      #     interval = "10s"
      #     timeout  = "2s"
      #   }
      # }

    }
  }
}
