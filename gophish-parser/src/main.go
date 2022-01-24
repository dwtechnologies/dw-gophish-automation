package main
 
import (
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"strings"
	"fmt"
	"github.com/aws/aws-lambda-go/events"
    "github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/ssm"
)

var (
	errNoSignature      = errors.New("No X-Gophish-Signature header provided")
	errInvalidSignature = errors.New("Invalid signature provided")
)

type SSMGetParameterAPI interface {
	GetParameter(ctx context.Context,
		params *ssm.GetParameterInput,
		optFns ...func(*ssm.Options)) (*ssm.GetParameterOutput, error)
}

type eventBody struct {
    Email   string          `json:"email"`
    Time    string          `json:"time"`
    Message string          `json:"message"`
    Details json.RawMessage `json:"details"`
}

func FindParameter(c context.Context, api SSMGetParameterAPI, input *ssm.GetParameterInput) (*ssm.GetParameterOutput, error) {
	return api.GetParameter(c, input)


}

func handleRequest(ctx context.Context, request events.ALBTargetGroupRequest) (events.ALBTargetGroupResponse, error) {
	fmt.Printf("Processing request data for traceId %s.\n", request.Headers["x-amzn-trace-id"])
	// Get the provided signature
	signatureHeader := request.Headers["x-gophish-signature"]
	if signatureHeader == "" {
		fmt.Printf(errNoSignature.Error())
		out := `{ "status": "` + errNoSignature.Error() + `" }`
		return events.ALBTargetGroupResponse{Body: out, StatusCode: 200, StatusDescription: "200 OK", IsBase64Encoded: false, Headers: map[string]string{"content-type": "application/json"}}, nil
	}
	
	signatureParts := strings.SplitN(signatureHeader, "=", 2)
	if len(signatureParts) != 2 {
		fmt.Printf(errInvalidSignature.Error())
		out := `{ "status": "` + errInvalidSignature.Error() + `" }`
		return events.ALBTargetGroupResponse{Body: out, StatusCode: 200, StatusDescription: "200 OK", IsBase64Encoded: false, Headers: map[string]string{"content-type": "application/json"}}, nil
	}
	
	signature := signatureParts[1]
	
	gotHash, err := hex.DecodeString(signature)
	if err != nil {
		fmt.Printf("Failed to Decode string")
		out := `{ "status": "Failed to Decode string" }`
		return events.ALBTargetGroupResponse{Body: out, StatusCode: 200, StatusDescription: "200 OK", IsBase64Encoded: false, Headers: map[string]string{"content-type": "application/json"}}, nil
	}
	
	// Copy out the request body so we can validate the signature
	fmt.Printf("Processing body \n %s.\n", request.Body)
	eb := &eventBody{}
	json.Unmarshal([]byte(request.Body), eb)
	body, err := json.Marshal(eb)
	fmt.Printf("Marshalled \n %s.\n", body)
	if err != nil {
		fmt.Printf("Failed to read Body")
		out := `{ "status": "Failed to read Body" }`
		return events.ALBTargetGroupResponse{Body: out, StatusCode: 200, StatusDescription: "200 OK", IsBase64Encoded: false, Headers: map[string]string{"content-type": "application/json"}}, nil
	}
	
	// Validate the signature
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		fmt.Printf("configuration error, " + err.Error())
		out := `{ "status": "configuration error ` + err.Error() + `" }`
		return events.ALBTargetGroupResponse{Body: out, StatusCode: 200, StatusDescription: "200 OK", IsBase64Encoded: false, Headers: map[string]string{"content-type": "application/json"}}, nil
	}
	client := ssm.NewFromConfig(cfg)

	input := &ssm.GetParameterInput{
		// Add your secret, SSM Parameter, with or without decryption
		Name: aws.String("<Your SSM Parameter>"),
		WithDecryption: true,
	}
	
	results, err := FindParameter(context.TODO(), client, input)
	if err != nil {
		fmt.Printf("configuration error, " + err.Error())
		out := `{ "status": "Failed to read SSM Parameter ` + err.Error() + `" }`
		return events.ALBTargetGroupResponse{Body: out, StatusCode: 200, StatusDescription: "200 OK", IsBase64Encoded: false, Headers: map[string]string{"content-type": "application/json"}}, nil
	}
	
	expectedMAC := hmac.New(sha256.New, []byte(*results.Parameter.Value))
	expectedMAC.Write(body)
	expectedHash := expectedMAC.Sum(nil)
	
	if !hmac.Equal(gotHash, expectedHash) {
		fmt.Printf("invalid signature provided. expected %s got %s", hex.EncodeToString(expectedHash), signature)
		out := `{ "status": "invalid signature provided" }`
		return events.ALBTargetGroupResponse{Body: out, StatusCode: 200, StatusDescription: "200 OK", IsBase64Encoded: false, Headers: map[string]string{"content-type": "application/json"}}, nil
	} else {
		fmt.Printf("Matches")
		out := `{ "status": "Matches" }`
		return events.ALBTargetGroupResponse{Body: out, StatusCode: 200, StatusDescription: "200 OK", IsBase64Encoded: false, Headers: map[string]string{"content-type": "application/json"}}, nil
	}
}

func main() {
        lambda.Start(handleRequest)
}