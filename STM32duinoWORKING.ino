#include <math.h>

long counter;
int old_arcus;
int HALL1;
int HALL2;
int new_arcus;
int offset = 790;
bool lock = 0;
int corse = 0;
int fine = 0;
int moveCondition = 0;

void setup() {
  HALL1 = analogRead(A0) - offset;
  HALL2 = analogRead(A1) - offset;
  new_arcus = atan2(HALL1, HALL2) * (180 / PI) + 180;
  old_arcus = new_arcus;
  Serial.begin(115200);
}

void loop() {
  HALL1 = analogRead(A0) - offset;
  HALL2 = analogRead(A1) - offset;
  new_arcus = atan2(HALL1, HALL2) * (180 / PI) + 180;

  moveCondition = new_arcus - old_arcus;
  if (moveCondition > 250) {
    corse += 360;
    fine = 0;
  }
  if (moveCondition < -250) {
    corse -= 360;
    fine = 0;
  }
  if (new_arcus < old_arcus) {
    fine++; //POSSIBLE INACURACY!
  }
  if (new_arcus > old_arcus) {
    fine--; //POSSIBLE INACURACY!
  }

  counter = corse + fine;
  Serial.println(counter);
  old_arcus = new_arcus;
}