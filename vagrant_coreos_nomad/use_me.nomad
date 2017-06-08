# THIS IS WORK IN PROGRESS AND DOES NOT WORK YET.

job "redgreen" {

  # ok
  datacenters = ["dc1"]

  # one per node
  type = "system"

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
        cpu    = 10  # 10 MHz
        memory = 25  # 25MB
        network {
          # this allocates a dynamic host port and maps it to the one in the
          # container with the same name ("server") as above. so you can map
          # multiple ports.
          port "server" {}
        }
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
