#include <Wire.h>
#include <FastLED.h>
#include <ezButton.h>

#define I2C_ADDRESS 0x42
#define NUM_LEDS 6

ezButton button1(5);
ezButton button2(6);

CRGB leds[NUM_LEDS];
uint8_t gHue = 0;

unsigned long lastAnimationTime = 0;
int animationStep = 0;

enum AnimationState {
  ANIM_OFF,
  ANIM_SLEEPING,
  ANIM_LISTENING,
  ANIM_RAINBOW,
  ANIM_TALKING,
  ANIM_THINKING,
  ANIM_BOOTING
};

AnimationState currentAnimation = ANIM_BOOTING;

void setup() {
  button1.setDebounceTime(50);
  button2.setDebounceTime(50);

  FastLED.addLeds<WS2812, 3, GRB>(leds, NUM_LEDS);

  Wire.begin(I2C_ADDRESS);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);
}

void loop() {
  unsigned long currentTime = millis();

  switch (currentAnimation) {
    case ANIM_OFF:
      FastLED.clear();
      break;

    case ANIM_BOOTING:
      // booting, before python is loaded
      sinelon();
      break;

    case ANIM_SLEEPING:
      // sleeping
      cascadeBreathing(.25, CRGB(120,120,120), CRGB(10,10,10));
      break;

    case ANIM_LISTENING:
      // awake 
      cascadeBreathing(.85, CRGB(0,255,255), CRGB(0,100,100));
      break;

    case ANIM_RAINBOW:
      rainbow();
      break;

    case ANIM_TALKING:
      juggle();
      break;

    case ANIM_THINKING:
      bpm();
      break;
  }

  FastLED.show();

  EVERY_N_MILLISECONDS( 10 ) { gHue++; }
  // checkButtons();
}


void checkButtons() {
  button1.loop();
  button2.loop();

  if (button1.isReleased()) {
    if (currentAnimation < ANIM_THINKING) {
      currentAnimation = static_cast<AnimationState>(currentAnimation + 1);
    } else {
      currentAnimation = ANIM_OFF; // Wrap around to the first state
    }
  }

  if (button2.isReleased()) {
    if (currentAnimation > ANIM_OFF) {
      currentAnimation = static_cast<AnimationState>(currentAnimation - 1);
    } else {
      currentAnimation = ANIM_THINKING;
    }
  }
}

void receiveEvent(int howMany) {
  if (howMany == 1) {
    byte receivedCode = Wire.read();
    
    switch (receivedCode) {
      case 0:
        currentAnimation = ANIM_OFF;
        break;
      case 1:
        currentAnimation = ANIM_BOOTING;
        break;
      case 2:
        currentAnimation = ANIM_SLEEPING;
        break;
      case 3:
        currentAnimation = ANIM_LISTENING;
        break;
      case 4:
        currentAnimation = ANIM_RAINBOW;
        break;
      case 5:
        currentAnimation = ANIM_TALKING;
        break;
      case 6:
        currentAnimation = ANIM_THINKING;
        break;
      default:
        break;
    }
  }
}

void requestEvent() {
  button1.loop();
  button2.loop();

  bool buttonState1 = button1.isPressed();
  bool buttonState2 = button2.isPressed();

  Wire.write(buttonState1 ? 1 : 0);
  Wire.write(buttonState2 ? 1 : 0);
}

void rainbow() 
{
  fill_rainbow( leds, NUM_LEDS, gHue, 7);
}

void sinelon()
{
  fadeToBlackBy( leds, NUM_LEDS, 20);
  int pos = beatsin16( 13, 0, NUM_LEDS-1 );
  leds[pos] += CHSV( gHue, 255, 192);
}

void juggle() {
  fadeToBlackBy( leds, NUM_LEDS, 20);
  uint8_t dothue = 0;
  for( int i = 0; i < 8; i++) {
    leds[beatsin16( i+7, 0, NUM_LEDS-1 )] |= CHSV(dothue, 200, 255);
    dothue += 32;
  }
}

void bpm()
{
  uint8_t BeatsPerMinute = 62;
  CRGBPalette16 palette = CloudColors_p;
  uint8_t beat = beatsin8( BeatsPerMinute, 64, 255);
  for( int i = 0; i < NUM_LEDS; i++) { //9948
    leds[i] = ColorFromPalette(palette, gHue+(i*2), beat-gHue+(i*10));
  }
}

void cascadeBreathing(float pulseSpeed, CRGB colorA, CRGB colorB) {
    static int currentLED = 0;
    static int direction = 1;

    CHSV hsvA = rgb2hsv_approximate(colorA);
    CHSV hsvB = rgb2hsv_approximate(colorB);

    float valueMin = hsvA.val;
    float valueMax = hsvB.val;
    static float delta = (valueMax - valueMin) / 2.35040238;

    float dV = ((exp(sin(pulseSpeed * millis() / 2000.0 * PI)) - 0.36787944) * delta);
    float val = valueMin + dV;
    uint8_t hue = map(val, valueMin, valueMax, hsvA.hue, hsvB.hue);
    uint8_t sat = map(val, valueMin, valueMax, hsvA.sat, hsvB.sat);

    leds[currentLED] = CHSV(hue, sat, val);
    leds[currentLED].r = dim8_video(leds[currentLED].r);
    leds[currentLED].g = dim8_video(leds[currentLED].g);
    leds[currentLED].b = dim8_video(leds[currentLED].b);

    currentLED += direction;
    if (currentLED == 0 || currentLED == NUM_LEDS - 1) {
        direction = -direction;
    }
}
