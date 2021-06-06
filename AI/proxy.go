// pattern 파일을 전달받고 사용자 상태를 파악한 후, 패턴분석 AI를 호출함
// service 보고 해당 service url로 연결
package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"os/exec"
	"strings"
	"time"

	_ "github.com/go-sql-driver/mysql"
)

var aServiceURL = "http://127.0.0.1:8000/accounts/signup/"
var bServiceURL = "http://127.0.0.1/main/"
var defaultURL = "http://127.0.0.1/"
var blockURL = "http://127.0.0.1/"

// Get the port to listen on
func getListenAddress() string {
	port := "8222"
	return ":" + port
}

// Log the env variables required for a reverse proxy
func logSetup() {
	log.Printf("Server will run on: %s\n", getListenAddress())
	log.Printf("Redirecting to A url: %s\n", aServiceURL)
	log.Printf("Redirecting to B url: %s\n", bServiceURL)
	log.Printf("Redirecting to Default url: %s\n", defaultURL)
	log.Printf("Redirecting to Block url: %s\n", blockURL)
}

type requestPayloadStruct struct {
	// 서비스 연결
	ServiceKind string `json:"service_kind"`
	UserID      string `json:"user_id"`
}
type sendDataStruct struct {
	// 알람(AI->server)
	User                string `json:"user"`
	Time                string `json:"time"`
	Mouse_prediction    string `json:"mouse_prediction"`
	Resource_prediction string `json:"resource_prediction"`
	Type                int    `json:"type"`
	Label               string `json:"label"`
	Mouse_file_list     string `json:"mouse_file_list"`
	Resource_file_list  string `json:"resource_file_list"`
}

// Get a json decoder for a given requests body
func requestBodyDecoder(request *http.Request) *json.Decoder {
	// Read body to buffer
	body, err := ioutil.ReadAll(request.Body)
	if err != nil {
		log.Printf("Error reading body: %v", err)
		panic(err)
	}

	// Because go lang is a pain in the ass if you read the body then any susequent calls
	// are unable to read the body again....
	request.Body = ioutil.NopCloser(bytes.NewBuffer(body))

	return json.NewDecoder(ioutil.NopCloser(bytes.NewBuffer(body)))
}

// Parse the requests body
func parseRequestBody(request *http.Request) requestPayloadStruct {
	decoder := requestBodyDecoder(request)
	var requestPayload requestPayloadStruct
	err := decoder.Decode(&requestPayload)
	if err != nil {
		panic(err)
	}
	return requestPayload
}

// Log the typeform payload and redirect url
func logRequestPayload(requestionPayload requestPayloadStruct, proxyURL string, blockState string) {
	log.Printf("service_kind: %s, user_id: %s, proxy_url: %s, block_state : %s\n", requestionPayload.ServiceKind, requestionPayload.UserID, proxyURL, blockState)
}

// Get the url for a given proxy condition
func getProxyURL(serviceKindRaw, blockState string) string {
	serviceKind := strings.ToUpper(serviceKindRaw)
	if blockState == "unvalid" {
		return blockURL
	}
	if serviceKind == "A" {
		return aServiceURL
	}
	if serviceKind == "B" {
		return bServiceURL
	}
	return defaultURL
}

// Serve a reverse proxy for a given url
func serveReverseProxy(target string, res http.ResponseWriter, req *http.Request) {
	// parse the url
	url, _ := url.Parse(target)
	fmt.Println(url)
	fmt.Println(req)
	fmt.Println("kkk")

	// create the reverse proxy
	proxy := httputil.NewSingleHostReverseProxy(url)

	// Update the headers to allow for SSL redirection
	req.URL.Host = url.Host
	req.URL.Scheme = url.Scheme
	req.Header.Set("X-Forwarded-Host", req.Header.Get("Host"))
	req.Host = url.Host

	// Note that ServeHttp is non blocking and uses a go routine under the hood
	proxy.ServeHTTP(res, req)
}

// Given a request send it to the appropriate url
func handleRequestAndRedirect(res http.ResponseWriter, req *http.Request) {
	requestPayload := parseRequestBody(req)
	blockState := getUserBlock(requestPayload.UserID)
	url := getProxyURL(requestPayload.ServiceKind, blockState)
	logRequestPayload(requestPayload, url, blockState)
	serveReverseProxy(url, res, req)
	// ... more to come
}

// DB user block 상태 확인
func getUserBlock(user string) string {
	// sql.DB 객체 생성
	id := os.Getenv("DB_USERNAME")
	pw := os.Getenv("DB_PASSWORD")
	host := "tcp(127.0.0.1:3306)"
	dbName := os.Getenv("DB_NAME")
	sqlQuery := id + ":" + pw + "@" + host + "/" + dbName
	db, err := sql.Open("mysql", sqlQuery)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()
	// 하나의 Row를 갖는 SQL 쿼리
	blockTF := 0
	sql := "SELECT is_active FROM " + dbName + ".accounts_user WHERE username = " + "'" + user + "'"
	err = db.QueryRow(sql).Scan(&blockTF)
	if err != nil {
		log.Fatal(err)
	}
	if blockTF == 1 {
		return "valid"
	}
	// block state가 True or 존재하지 않는 user
	return "unvalid"
}

func patternHandler(res http.ResponseWriter, req *http.Request) {
	err := req.ParseMultipartForm(4096)
	if err != nil {
		fmt.Println("error parse")
		panic(err)
	}
	if err != nil {
		fmt.Println("error")
		panic(err)
	}
	userID := req.FormValue("user_id")
	fmt.Println("user: ", userID)
	blockState := getUserBlock(userID)
	// user가 차단 상태면 bypass 확인x, 파일 저장x, AI 분석x
	if blockState == "unvalid" {
		return
	}
	by_pass := checkByPass(req)
	savePatternFile(userID, "mouse_pattern", "mouse", req)
	savePatternFile(userID, "resource_pattern", "resource", req)
	res.Write([]byte("Done!"))
	aiCall(userID, by_pass)
	fmt.Println("Finish Pattern Handling")
}

// by-pass 권 소유 확인
func checkByPass(req *http.Request) string {
	by_pass := "FAIL"
	token, err := req.Cookie("jwt")
	if err != nil {
		fmt.Println("no check bypass")
		return by_pass
	}
	url := "http://localhost:8000/api/token/verify/"
	tmpStr := strings.Split(token.String(), `=`)
	tokenStr := tmpStr[1]
	var jsonStr = []byte(`{"token": "` + tokenStr + `"}`)
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(jsonStr))
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode == 200 {
		by_pass = "PASS"
	}
	return by_pass
}

// pattern file save (C:\Users\user\Desktop\EEE\pred\mouse(resource)\user\~.csv)
func savePatternFile(userID, fileID, kind string, req *http.Request) {
	path := ".\\pred\\" + kind + "\\" + userID + "\\"
	if _, err := os.Stat(path); os.IsNotExist(err) {
		os.MkdirAll(path, os.ModeDir|0755)
	}
	t := time.Now().Format("20060102-150405")
	filename := t + ".csv"
	writePath := path + filename
	patternFile, _, err := req.FormFile(fileID)
	if err != nil {
		fmt.Println("there")
		panic(err)
	}
	defer patternFile.Close()
	// 파일 생성
	file, err := os.Create(writePath)
	if err != nil {
		panic(err)
	}
	io.Copy(file, patternFile)
	defer file.Close()
	fmt.Println(kind + " Save!!")
}

// ai_pred_pattern.py 실행
func aiCall(userID, by_pass string) {
	path := ".\\ai_pred_pattern.py"
	cmd := exec.Command("python", path, userID, by_pass)
	fmt.Println(cmd.Args)

	// // AI 호출 결과 기다리면서 출력
	// stdout, err := cmd.StdoutPipe()
	// if err != nil {
	// 	panic(err)
	// }
	// stderr, err := cmd.StderrPipe()
	// if err != nil {
	// 	panic(err)
	// }
	// cmd 끝나는걸 기다리지 않음 -> client는 ai 판단 끝날 때까지 기다리지 않아도 됨
	err := cmd.Start()
	if err != nil {
		panic(err)
	}
	// go copyOutput(stdout)
	// go copyOutput(stderr)
	// cmd.Wait()
}

// func copyOutput(r io.Reader) {
// 	scanner := bufio.NewScanner(r)
// 	for scanner.Scan() {
// 		fmt.Println(scanner.Text())
// 	}
// }

// AI에서 서버로 알람 대신 전달
func certHandler(res http.ResponseWriter, req *http.Request) {
	// request에서 sendData 추출
	decoder := requestBodyDecoder(req)
	var sendData sendDataStruct
	err := decoder.Decode(&sendData)
	if err != nil {
		panic(err)
	}

	// sendData 검증 과정 추가 필요@@

	// struct를 json으로 변경
	jsonStr, err := json.Marshal(sendData)
	if err != nil {
		panic(err)
	}
	fmt.Println(string(jsonStr))
	// server로 sendData 전송
	url := "http://127.0.0.1:8000/main/add/" // 관리자페이지
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(jsonStr))
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	fmt.Println("Finish CERT Handling")
}

func main() {
	// Log setup values
	fmt.Println("Starting Proxy Server...")
	// logSetup()
	http.HandleFunc("/service", handleRequestAndRedirect)

	// Upload route
	// 접속 localhost:8222/pattern
	http.HandleFunc("/pattern", patternHandler)
	// forward from AI to server
	http.HandleFunc("/cert", certHandler)
	if err := http.ListenAndServe(getListenAddress(), nil); err != nil {
		panic(err)
	}

}
