package main

import (
	"fmt"
	"net/http"
	"os"
	"strconv"
	"strings"

	"bytes"

	"runtime/debug"

	"github.com/gorilla/mux"
)

var color string = "a multi-colored shine on all surfaces"
var allocations map[string]bytes.Buffer
var count int

func handleHealth(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "OK")
}

func handleRoot(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, color)
}

func handleAllocate(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	amount, err := strconv.Atoi(vars["amount"])
	if err != nil {
		w.WriteHeader(400)
		fmt.Fprintf(w, "Invalid argument, amount should be an integer")
	}

	buf := bytes.Buffer{}
	buf.Grow(amount)
	count = count + 1
	id := fmt.Sprintf("%d", count)
	allocations[id] = buf
	fmt.Fprintf(w, id)
}

func handleDeallocate(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]
	if _, ok := allocations[id]; ok {
		delete(allocations, id)
		fmt.Fprintf(w, "OK")
	}

	w.WriteHeader(404)
	fmt.Fprintf(w, "not found")
}

func handleClear(w http.ResponseWriter, r *http.Request) {

	for key := range allocations {
		delete(allocations, key)
	}
	debug.FreeOSMemory()
	fmt.Fprintf(w, "OK")
}

func handleAllocations(w http.ResponseWriter, r *http.Request) {
	var total int
	for key, value := range allocations {
		total = total + value.Cap()
		fmt.Fprintf(w, fmt.Sprintf("%s => %d\n", key, value.Cap()))
	}
	fmt.Fprintf(w, fmt.Sprintf("total %d\n", total))
}

func main() {
	if len(os.Args) > 1 && os.Args[1] != "default" {
		color = strings.ToUpper(os.Args[1])
	}

	allocations = make(map[string]bytes.Buffer)

	r := mux.NewRouter()

	r.HandleFunc("/", handleRoot)
	r.HandleFunc("/health", handleHealth)
	r.HandleFunc("/allocate/{amount}", handleAllocate).Methods("GET")
	r.HandleFunc("/deallocate/{id}", handleDeallocate).Methods("GET")
	r.HandleFunc("/clear", handleClear)
	r.HandleFunc("/allocations", handleAllocations)
	http.Handle("/", r)
	_ = http.ListenAndServe(":8080", nil)
}
