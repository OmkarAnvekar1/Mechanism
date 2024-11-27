#include <WiFi.h>
#include <WiFiUdp.h>

// Wi-Fi credentials
const char* ssid = "abcde";
const char* password = "abcde123";

// UDP settings
WiFiUDP udp;
unsigned int localUdpPort = 12345; // Port to listen on
char incomingPacket[255];          // Buffer for incoming packets

// Relay pins
#define RELAY_PIN_CW 12   // Clockwise relay pin
#define RELAY_PIN_CCW 14  // Anticlockwise relay pin

void setup() {
  Serial.begin(115200);

  // Set relay pins as outputs
  pinMode(RELAY_PIN_CW, OUTPUT);
  pinMode(RELAY_PIN_CCW, OUTPUT);

  // Ensure both relays are off initially
  digitalWrite(RELAY_PIN_CW, LOW);
  digitalWrite(RELAY_PIN_CCW, LOW);

  // Connect to Wi-Fi
  Serial.println("Connecting to Wi-Fi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Attempting to connect to Wi-Fi...");
  }

  // Print IP address
  Serial.println("Connected to Wi-Fi!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // Start UDP
  udp.begin(localUdpPort);
  Serial.printf("Listening on UDP port %d\n", localUdpPort);
}

void loop() {
  int packetSize = udp.parsePacket();
  if (packetSize) {
    // Read the incoming packet
    int len = udp.read(incomingPacket, 255);
    if (len > 0) {
      incomingPacket[len] = '\0'; // Null-terminate the string
    }
    Serial.printf("Received: %s\n", incomingPacket);

    // Command handling
    if (strcmp(incomingPacket, "CW") == 0) { 
      digitalWrite(RELAY_PIN_CW, HIGH);
      digitalWrite(RELAY_PIN_CCW, LOW);
    } else if (strcmp(incomingPacket, "CCW") == 0) { 
      digitalWrite(RELAY_PIN_CW, LOW);
      digitalWrite(RELAY_PIN_CCW, HIGH);
    } else if (strcmp(incomingPacket, "STOP") == 0) {
      digitalWrite(RELAY_PIN_CW, LOW);
      digitalWrite(RELAY_PIN_CCW, LOW);
    }
  }
}
