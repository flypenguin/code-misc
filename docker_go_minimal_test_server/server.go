package main

import (
	"fmt"
	"net/http"
	"os"
	"strings"
)

var my_color string = "a multi-colored shine on all surfaces"

func handler_health(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "OK")
}

func handler_root(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, my_color)
}

func main() {
	if len(os.Args) > 1 && os.Args[1] != "default" {
		my_color = strings.ToUpper(os.Args[1])
	}
	http.HandleFunc("/", handler_root)
	http.HandleFunc("/health", handler_health)
	http.ListenAndServe(":8080", nil)
}
