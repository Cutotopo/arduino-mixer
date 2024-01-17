#include <LiquidCrystal.h>
#include <string.h>

#define TOTPM 4 // Total number of connected potentiometers
#define SONG_CHAR_LEN 300 // Maximum length of a songInfo string
#define SRCS_CHAR_LEN 50 // Maximum length of each source name

// Definition of each potentiometer's pin and their default values
int pms[] = {A0, A1, A2, A3}; // Pins where the potentiometers are connected
int pVal[TOTPM]; // Array for the potentiometer values

// songInfo string
char song[SONG_CHAR_LEN];

// Source labels
char srcs[TOTPM][SRCS_CHAR_LEN];

// Variables to control pages showing on the screen
int lastPage = -1;
int pageCycles = 0;
int maxPageCycles = 10;

// Variables to control the marquee effect for long text on the home screen
int trackHomeCycles = 0;
int currentTitlePos = 0;
int currentArtistPos = 0;
int currentTitleLength = 0;
int currentArtistLength = 0;

// Initialize the LCD screen
LiquidCrystal lcd(2, 3, 4, 5, 6, 7);

void setup() {
  // Begin serial
  Serial.begin(9600);

  // Set the number of columns and rows of the display
  lcd.begin(16, 2);

  // Print a message to the LCD while we wait for the PC to open the serial communication
  lcd.setCursor(0, 0);
  lcd.print("Ready!");
  lcd.setCursor(0, 1);
  lcd.print("Waiting for PC...");

  // Wait for the serial communication to begin
  while (Serial.available() == 0) {
    Serial.println("{\"t\":\"r\"}");
    delay(500);
  }

  // Read the config from serial
  lcd.setCursor(0, 0);
  lcd.print("PC connected.");
  lcd.setCursor(0, 1);
  lcd.print("Reading config...");
  for (int i = 0; i < TOTPM; i++) {
    pVal[i] = 0;
    for (int j = 0; Serial.available(); j++) {
      char currentChar = Serial.read();
      if (currentChar == '\n') {
        srcs[i][j] = '\0';
        break;
      } else {
        srcs[i][j] = currentChar;
      }
      // Wait for Arduino to read everything from serial
      delay(200);
    }
  }

  // Request metadata
  lcd.setCursor(0, 0);
  lcd.print("PC connected.");
  lcd.setCursor(0, 1);
  lcd.print("Reading meta...");
  while (Serial.available() == 0) {
    Serial.println("{\"t\":\"m\"}");
    delay(500);
  }
  lcd.clear();
}

void emptySongChar(int a) {
  // Empties the unused portion of the songInfo char
  for (int i = a; i < SONG_CHAR_LEN; i++) {
    song[i] = ' ';
  }
}

void renderVolume(int i, int v) {
  // Renders the volume page
  maxPageCycles = 25;
  lastPage = i + 1;
  pageCycles = 0;
  char out[50];
  sprintf(out, "{\"t\":\"v\",\"ch\":%d,\"val\":%d}", i, v);
  Serial.println(out);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(srcs[i]);
  lcd.setCursor(0, 1);
  lcd.print(v);
  lcd.print("%");
}

void renderHome(int updatePositions) {
  // Renders the home page (the songInfo screen)
  maxPageCycles = 10;
  lastPage = 0;
  pageCycles = 0;
  lcd.clear();
  lcd.setCursor(0, 0);

  // Implement the marquee effects for titles longer than 16 characters
  if (currentTitleLength > 16) {
    if (currentTitlePos >= currentTitleLength - 16) {
      currentTitlePos = 0;
    } else {
      if (updatePositions) {
        currentTitlePos++;
      }
    }
  }
  if (currentArtistLength > 16) {
    if (currentArtistPos >= currentArtistLength - 16) {
      currentArtistPos = 0;
    } else {
      if (updatePositions) {
        currentArtistPos++;
      }
    }
  }

  // Print data to the LCD
  int isArtist = 0;
  int artistChars = 0;
  int titleChars = 0;
  for (int i = 0; i < strlen(song); i++) {
    if (song[i] == '\v') {
      lcd.setCursor(0, 1);
      isArtist = 1;
      continue;
    }
    if (isArtist) {
      if (artistChars < 18) {
        lcd.print(song[i + currentArtistPos]);
        artistChars++;
      }
    } else {
      if (titleChars < 18) {
        lcd.print(song[i + currentTitlePos]);
        titleChars++;
      }
    }
  }
}

void renderHome() {
  renderHome(1);
}

// Count characters for the title (0) or artist (1)
int getSongInfoLength(int i) {
  int currentStrType = 0;
  int lengths[] = {0, 0};
  for (int i = 0; i < strlen(song); i++) {
    if (song[i] == '\v') {
      currentStrType = 1;
    } else {
      lengths[currentStrType]++;
    }
  }
  return lengths[i];
}

void loop() {
  // Check if there is any data available to be read from serial
  if (Serial.available() > 0) {
    delay(100);
    emptySongChar(Serial.available());
    for (int i = 0; Serial.available() > 0; i++) {
      char currentChar = Serial.read();
      if (currentChar == '\n') {
        song[i] = '\0';
      } else {
        song[i] = currentChar;
      }
    }
    // Calculate length of songInfo to decide if the marquee effect should be enabled
    currentTitlePos = 0;
    currentArtistPos = 0;
    currentTitleLength = getSongInfoLength(0);
    currentArtistLength = getSongInfoLength(1);
    if (currentTitleLength > 16 || currentArtistLength > 16) {
      trackHomeCycles = 1;
    } else {
      trackHomeCycles = 0;
    }
    // Render home page
    renderHome(0);
  }

  // Check the value of each potentiometer connected to the Arduino
  for (int i = 0; i < TOTPM; i++) {
    int cVal = map(analogRead(pms[i]), 0, 1015, 0, 50) * 2;
    // If it is different than its previous value, send the new value to the PC
    if (pVal[i] != cVal) {
      pVal[i] = cVal;
      renderVolume(i, cVal);
    }
  }

  // If the page is not the homepage, we should increase the pageCycles counter and when we reach maxPageCycles go back to the homepage automatically
  if (lastPage != 0 || trackHomeCycles == 1) {
    pageCycles++;
    if (pageCycles > maxPageCycles) {
      renderHome();
    }
  }

  // Sleep before checking serial again
  delay(100);
}
