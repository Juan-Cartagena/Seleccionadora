/*PROGRAM TO CONTROL A FURUTA PENDULUM*/
#include <stdio.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include <LiquidCrystal.h>
LiquidCrystal lcd(48, 49, 45, 44, 43, 42);
/*encoder pins*/
int PUL_Banda=8;
int PUL_Dosificador=7;
int DIR_Banda=9;
int DIR_Dosificador=6;

bool conveyor =0;

int Actuador[18];
int t_delay=220;
int t_on=105;

int retraso_dosificador=0;

int Act_1=53;
int Act_2=52;
int Act_3=51;
int Act_4=50;
int Act_5=49;
int Act_6=48;
int Act_7=47;
int Act_8=46;
int Act_9=45;
int Act_10=44;
int Act_11=43;
int Act_12=42;
int Act_13=41;
int Act_14=40;
int Act_15=39;
int Act_16=38;
int Act_17=37;
int Act_18=36;

int test=0;
String entradaSerial = "";         // String para almacenar entrada
bool entradaCompleta = false;  // Indicar si el String está completo


const int s=53;
volatile float count_2 =0.0;
volatile float count_1=0.0;
const float dt=1;
/*PID_1 gains*/
const float kp_1=5.0;
const float ki_1=0.0;//0.0*n;
const float kd_1=0.8;//0.5/n;
/*PID_2 gains*/
const float kp_2=40;//60.0;
const float ki_2=2;//4.0*n;
const float kd_2=2.0;//2.0/n;
long i=0;
int t=100;
float setpoint_theta=180;
float setpoint_alpha=0;
/*PID variables*/
volatile float alpha=0,error1=0,lastE1=0,Area_1=0,Int_E1=0,Der_E1=0,out1=0;
volatile float theta=0,error2=0,lastE2=0,Area_2=0,Int_E2=0,Der_E2=0,out2=0;

ISR(TIMER3_COMPA_vect)
{ sei();
digitalWrite(10,!digitalRead(10));
  if(conveyor==1){
    digitalWrite(PUL_Banda,!digitalRead(PUL_Banda));
    retraso_dosificador++;
    if(retraso_dosificador==2){
      retraso_dosificador=0;
      digitalWrite(PUL_Dosificador,!digitalRead(PUL_Dosificador));
      }
    
    }
  for(int a = 0; a<18;a++){
    if(Actuador[a]>0){Actuador[a]--;}
    }
  if(Actuador[0]==t_on){digitalWrite(Act_1,HIGH);}
  if(Actuador[1]==t_on){digitalWrite(Act_2,HIGH);}
  if(Actuador[2]==t_on){digitalWrite(Act_3,HIGH);}
  if(Actuador[3]==t_on){digitalWrite(Act_4,HIGH);}
  if(Actuador[4]==t_on){digitalWrite(Act_5,HIGH);}
  if(Actuador[5]==t_on){digitalWrite(Act_6,HIGH);}
  if(Actuador[6]==t_on){digitalWrite(Act_7,HIGH);}
  if(Actuador[7]==t_on){digitalWrite(Act_8,HIGH);}
  if(Actuador[8]==t_on){digitalWrite(Act_9,HIGH);}
  if(Actuador[9]==t_on){digitalWrite(Act_10,HIGH);}
  if(Actuador[10]==t_on){digitalWrite(Act_11,HIGH);}
  if(Actuador[11]==t_on){digitalWrite(Act_12,HIGH);}
  if(Actuador[12]==t_on){digitalWrite(Act_13,HIGH);}
  if(Actuador[13]==t_on){digitalWrite(Act_14,HIGH);}
  if(Actuador[14]==t_on){digitalWrite(Act_15,HIGH);}
  if(Actuador[15]==t_on){digitalWrite(Act_16,HIGH);}
  if(Actuador[16]==t_on){digitalWrite(Act_17,HIGH);}
  if(Actuador[17]==t_on){digitalWrite(Act_18,HIGH);}

if(test==0){
  if(Actuador[0]==0){digitalWrite(Act_1,LOW);}
  if(Actuador[1]==0){digitalWrite(Act_2,LOW);}
  if(Actuador[2]==0){digitalWrite(Act_3,LOW);}
  if(Actuador[3]==0){digitalWrite(Act_4,LOW);}
  if(Actuador[4]==0){digitalWrite(Act_5,LOW);}
  if(Actuador[5]==0){digitalWrite(Act_6,LOW);}
  if(Actuador[6]==0){digitalWrite(Act_7,LOW);}
  if(Actuador[7]==0){digitalWrite(Act_8,LOW);}
  if(Actuador[8]==0){digitalWrite(Act_9,LOW);}
  if(Actuador[9]==0){digitalWrite(Act_10,LOW);}
  if(Actuador[10]==0){digitalWrite(Act_11,LOW);}
  if(Actuador[11]==0){digitalWrite(Act_12,LOW);}
  if(Actuador[12]==0){digitalWrite(Act_13,LOW);}
  if(Actuador[13]==0){digitalWrite(Act_14,LOW);}
  if(Actuador[14]==0){digitalWrite(Act_15,LOW);}
  if(Actuador[15]==0){digitalWrite(Act_16,LOW);}
  if(Actuador[16]==0){digitalWrite(Act_17,LOW);}
  if(Actuador[17]==0){digitalWrite(Act_18,LOW);}
}
}
void setup()
{//Serial.begin(9600);
  pinMode(13,OUTPUT);
  pinMode(10,OUTPUT);
  /*channels A and B as inputs*/
  pinMode(PUL_Banda, OUTPUT); 
  pinMode(PUL_Dosificador, OUTPUT);
  pinMode(DIR_Banda, OUTPUT); 
  pinMode(DIR_Dosificador, OUTPUT);
  /*Actuadores como salida*/
  pinMode(Act_1, OUTPUT);digitalWrite(Act_1,LOW);
  pinMode(Act_2, OUTPUT);digitalWrite(Act_2,LOW);
  pinMode(Act_3, OUTPUT);digitalWrite(Act_3,LOW);
  pinMode(Act_4, OUTPUT);digitalWrite(Act_4,LOW);
  pinMode(Act_5, OUTPUT);digitalWrite(Act_5,LOW);
  pinMode(Act_6, OUTPUT);digitalWrite(Act_6,LOW);
  pinMode(Act_7, OUTPUT);digitalWrite(Act_7,LOW);
  pinMode(Act_8, OUTPUT);digitalWrite(Act_8,LOW);
  pinMode(Act_9, OUTPUT);digitalWrite(Act_9,LOW);
  pinMode(Act_10, OUTPUT);digitalWrite(Act_10,LOW);
  pinMode(Act_11, OUTPUT);digitalWrite(Act_11,LOW);
  pinMode(Act_12, OUTPUT);digitalWrite(Act_12,LOW);
  pinMode(Act_13, OUTPUT);digitalWrite(Act_13,LOW);
  pinMode(Act_14, OUTPUT);digitalWrite(Act_14,LOW);
  pinMode(Act_15, OUTPUT);digitalWrite(Act_15,LOW);
  pinMode(Act_16, OUTPUT);digitalWrite(Act_16,LOW);
  pinMode(Act_17, OUTPUT);digitalWrite(Act_17,LOW);
  pinMode(Act_18, OUTPUT);digitalWrite(Act_18,LOW);



  Serial.begin(115200);
  Serial.setTimeout(1);



  
  /*pins to H-bridge as outputs*/
  DDRH=DDRH|B00111000;//PH5=D PH4=B PH3=P
  TCCR4A|=(1<<COM4A1)|(1<<WGM40);
  TCCR4B=0x02;//TCCR4B|=(1<<CS41)|(1<<CS40);
  /*to set ISR*/
  TCCR3A=0;
  TCCR3B=0;
  OCR3A=2000*dt;
  TCCR3B |= (1<<WGM32);
  TCCR3B |= (0<<CS30);
  TCCR3B |= (1<<CS31);
  TIMSK3=(1<<OCIE3A);
  sei();
  digitalWrite(DIR_Banda,HIGH);
  digitalWrite(DIR_Dosificador,LOW);

// Serial.begin(9600);
}
void loop()
{
if(test==1){
digitalWrite(13,!digitalRead(13));
digitalWrite(Act_1,HIGH);delay(t);digitalWrite(Act_1,LOW);
digitalWrite(Act_2,HIGH);delay(t);digitalWrite(Act_2,LOW);
digitalWrite(Act_3,HIGH);delay(t);digitalWrite(Act_3,LOW);
digitalWrite(Act_4,HIGH);delay(t);digitalWrite(Act_4,LOW);
digitalWrite(Act_5,HIGH);delay(t);digitalWrite(Act_5,LOW);
digitalWrite(Act_6,HIGH);delay(t);digitalWrite(Act_6,LOW);
digitalWrite(Act_7,HIGH);delay(t);digitalWrite(Act_7,LOW);
digitalWrite(Act_8,HIGH);delay(t);digitalWrite(Act_8,LOW);
digitalWrite(Act_9,HIGH);delay(t);digitalWrite(Act_9,LOW);
digitalWrite(Act_10,HIGH);delay(t);digitalWrite(Act_10,LOW);
digitalWrite(Act_11,HIGH);delay(t);digitalWrite(Act_11,LOW);
digitalWrite(Act_12,HIGH);delay(t);digitalWrite(Act_12,LOW);
digitalWrite(Act_13,HIGH);delay(t);digitalWrite(Act_13,LOW);
digitalWrite(Act_14,HIGH);delay(t);digitalWrite(Act_14,LOW);
digitalWrite(Act_15,HIGH);delay(t);digitalWrite(Act_15,LOW);
digitalWrite(Act_16,HIGH);delay(t);digitalWrite(Act_16,LOW);
digitalWrite(Act_17,HIGH);delay(t);digitalWrite(Act_17,LOW);
//digitalWrite(Act_18,HIGH);delay(t);digitalWrite(Act_18,LOW);
delay(1000);
}
  if (entradaCompleta) {
    if (entradaSerial == "C1\n") {Serial.print("conveyor ON\n");conveyor=1;}
    else if (entradaSerial == "C0\n"){Serial.print("conveyor OFF\n");conveyor=0;}
    else if (entradaSerial == "T1\n"){Serial.print("Test Actuadores ON\n");test=1;}
    else if (entradaSerial == "T0\n"){Serial.print("Test Actuadores OFF\n");test=0;}
    else if (entradaSerial == "M1\n") {Serial.print("Grano Malo Fila 1\n");Actuador[0]=t_delay;}
    else if (entradaSerial == "M2\n") {Serial.print("Grano Malo Fila 2\n");Actuador[0]=t_delay; Actuador[1]=t_delay;}
    else if (entradaSerial == "M3\n") {Serial.print("Grano Malo Fila 3\n");Actuador[1]=t_delay;}
    else if (entradaSerial == "M4\n") {Serial.print("Grano Malo Fila 4\n");Actuador[1]=t_delay; Actuador[2]=t_delay;}
    else if (entradaSerial == "M5\n") {Serial.print("Grano Malo Fila 5\n");Actuador[2]=t_delay;}
    else if (entradaSerial == "M6\n") {Serial.print("Grano Malo Fila 6\n");Actuador[2]=t_delay; Actuador[3]=t_delay;}
    else if (entradaSerial == "M7\n") {Serial.print("Grano Malo Fila 7\n");Actuador[3]=t_delay;}
    else if (entradaSerial == "M8\n") {Serial.print("Grano Malo Fila 8\n");Actuador[3]=t_delay; Actuador[4]=t_delay;}
    else if (entradaSerial == "M9\n") {Serial.print("Grano Malo Fila 9\n");Actuador[4]=t_delay;}
    else if (entradaSerial == "M10\n") {Serial.print("Grano Malo Fila 10\n");Actuador[4]=t_delay; Actuador[5]=t_delay;}
    else if (entradaSerial == "M11\n") {Serial.print("Grano Malo Fila 11\n");Actuador[5]=t_delay;}
    else if (entradaSerial == "M12\n") {Serial.print("Grano Malo Fila 12\n");Actuador[5]=t_delay; Actuador[6]=t_delay;}
    else if (entradaSerial == "M13\n") {Serial.print("Grano Malo Fila 13\n");Actuador[6]=t_delay;}
    else if (entradaSerial == "M14\n") {Serial.print("Grano Malo Fila 14\n");Actuador[6]=t_delay; Actuador[7]=t_delay;}
    else if (entradaSerial == "M15\n") {Serial.print("Grano Malo Fila 15\n");Actuador[7]=t_delay;}
    else if (entradaSerial == "M16\n") {Serial.print("Grano Malo Fila 16\n");Actuador[7]=t_delay; Actuador[8]=t_delay;}
    else if (entradaSerial == "M17\n") {Serial.print("Grano Malo Fila 17\n");Actuador[8]=t_delay;}
    else if (entradaSerial == "M18\n") {Serial.print("Grano Malo Fila 18\n");Actuador[8]=t_delay; Actuador[9]=t_delay;}
    else if (entradaSerial == "M19\n") {Serial.print("Grano Malo Fila 19\n");Actuador[9]=t_delay;}
    else if (entradaSerial == "M20\n") {Serial.print("Grano Malo Fila 20\n");Actuador[9]=t_delay; Actuador[10]=t_delay;}
    else if (entradaSerial == "M21\n") {Serial.print("Grano Malo Fila 21\n");Actuador[10]=t_delay;}
    else if (entradaSerial == "M22\n") {Serial.print("Grano Malo Fila 22\n");Actuador[10]=t_delay; Actuador[11]=t_delay;}
    else if (entradaSerial == "M23\n") {Serial.print("Grano Malo Fila 23\n");Actuador[11]=t_delay;}
    else if (entradaSerial == "M24\n") {Serial.print("Grano Malo Fila 24\n");Actuador[11]=t_delay; Actuador[12]=t_delay;}
    else if (entradaSerial == "M25\n") {Serial.print("Grano Malo Fila 25\n");Actuador[12]=t_delay;}
    else if (entradaSerial == "M26\n") {Serial.print("Grano Malo Fila 26\n");Actuador[12]=t_delay; Actuador[13]=t_delay;}
    else if (entradaSerial == "M27\n") {Serial.print("Grano Malo Fila 27\n");Actuador[13]=t_delay;}
    else if (entradaSerial == "M28\n") {Serial.print("Grano Malo Fila 28\n");Actuador[13]=t_delay; Actuador[14]=t_delay;}
    else if (entradaSerial == "M29\n") {Serial.print("Grano Malo Fila 29\n");Actuador[14]=t_delay;}
    else if (entradaSerial == "M30\n") {Serial.print("Grano Malo Fila 30\n");Actuador[14]=t_delay; Actuador[15]=t_delay;}
    else if (entradaSerial == "M31\n") {Serial.print("Grano Malo Fila 31\n");Actuador[15]=t_delay;}
    else if (entradaSerial == "M32\n") {Serial.print("Grano Malo Fila 32\n");Actuador[15]=t_delay; Actuador[16]=t_delay;}
    else if (entradaSerial == "M33\n") {Serial.print("Grano Malo Fila 33\n");Actuador[16]=t_delay;}
    else if (entradaSerial == "M34\n") {Serial.print("Grano Malo Fila 34\n");Actuador[16]=t_delay; Actuador[17]=t_delay;}
    else if (entradaSerial == "M35\n") {Serial.print("Grano Malo Fila 35\n");Actuador[17]=t_delay;}


    
    else { // Cualquier otro dato recibido
    Serial.println("El dato recibido es inválido!!");
    }
    entradaSerial = "";
    entradaCompleta = false;
  }

}

void serialEvent() {
  while (Serial.available()) {
    // Obtener bytes de entrada:
    char inChar = (char)Serial.read();
    // Agregar al String de entrada:
    entradaSerial += inChar;
    // Para saber si el string está completo, se detendrá al recibir
    // el caracter de retorno de línea ENTER \n
    if (inChar == '\n') {
      entradaCompleta = true;
    }
  }
}
