#include <SPI.h>
#include <Ethernet.h>

#define duty_cycle 0.6
#define LEFT HIGH
#define RIGHT LOW

/*
************************************************************************
********************************PINES***********************************
************************************************************************

Pines de salida: 
Step       -  Pin 9
Enable     -  Pin 8
Direccion  -  Pin 7

Pines de entrada
Switch 1   -  Pin 6
Switch 2   -  Pin 5
*/

int Step  = 9;
int En = 8;
int Dir = 7;
int Switch = 6;
int Switch2 = 5;

/*
************************************************************************
******************************VARIABLES*********************************
************************************************************************

pos        -  numero de pasos que el motor se ha movido
pos_in     -  posicion inicial de movimiento del motor (en pasos)
pos_fin    -  posicion final de movimiento de motor (en pasos)
n_pos_int  -  numero de posiciones intermedias de movimiento (en pasos)
freq       -  frecuencias para movimiento del motor
Direction  -  direccion de movimiento
*/

long pasos_total = 0;
long pasos_tope = 0;
int freq = 3000;

String dato ="";
char c;

byte mac[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
byte ip[] = {10, 10, 40, 245};
byte gateway[] = {10, 10, 40, 1};
byte subnet[] = {255, 255, 255, 0};

EthernetServer server = EthernetServer(12345);

/*
************************************************************************
***********************COMANDOS PARA MOVIMIENTO*************************
************************************************************************

Tabla de comandos para control del motor:

    0x00    MOVER
    0x01    PARAR
    0x02    CALIBRAR
    
*/

void setup() 
{
  pinMode(Step, OUTPUT);
  pinMode(Dir, OUTPUT);
  pinMode(En, OUTPUT);
  pinMode(Switch, INPUT);
  pinMode(Switch2, INPUT);
  
  digitalWrite(Switch, LOW);
  digitalWrite(Switch2, LOW);
  digitalWrite(En, LOW);
  
  Ethernet.begin(mac, ip, gateway, subnet);
  server.begin();
}

void loop() 
{ 
  EthernetClient client = server.available();

  if (client)
  {
    while (client.connected())
    {
      if (client.available())
      {
        c = char(client.read());
        dato = dato + c;
      }        
      if (c == '\n')
        break;
    }
  }
  
  if (dato.charAt(0) == '0')
  {  
    if (dato.substring(dato.length() - 1, dato.length() - 2) == "L")
    {
      mover_motor(dato.substring(1, dato.length() - 2).toInt(), LEFT, client);
      server.println("OK\n");
    }

    if (dato.substring(dato.length() - 1, dato.length() - 2) == "R")
    {
      mover_motor(dato.substring(1, dato.length() - 2).toInt(), RIGHT, client);
      server.println("OK\n");      
    }    
  }
  
  if (dato.charAt(0) == '1')
  {
    dato = "";
    calibrar_motor(LEFT, client);
    server.print(String(pasos_tope) + '\n');
  }
  
  if (dato.charAt(0) == '2')
  {
    dato = "";
    motor_inicio(client);
    server.print("OK\n");
  }
}

void mover_motor(long pasos, bool Direction, EthernetClient client)
{ 
  //Desactivar las interrupciones y configurar el timer con los parametros
  //determinados por las constantes globales freq y duty_cycle  
  pasos_total = 0;
  encender_timer();
  //Activar las interrupciones y activar el movimiento del motor
  digitalWrite(Dir, Direction);
  //Mientras el pasos que haya contado la interrupcion sea menor 
  //a la distancia que se desea mover el deslizador, esperar
  while (1)
  {     
    if (client)
    {
      while (client.connected())
      {
        if (client.available())
        {
          c = char(client.read());
          dato = dato + c;
        }        
        if (c == '\n')
          break;
      }      
    }   

    if (dato.charAt(0) == '3')
    {
      apagar_timer();
      dato = "";
      return;
    }   
    
    if ((pasos_total == pasos) || (digitalRead(Switch) == HIGH || digitalRead(Switch2) == HIGH))
    {
      apagar_timer();
      break;
    }
  }  
  //Una vez que se haya alcanzado la distancia requerida, detener
  //el motor, apagar el timer y desactivar la interrupcion de conteo
  //de pasos. Resetear el conteo hecho por la rutina de interrupcion
  //y resetear el valor del numero de pasos que se busca leer
  pasos_total = 0;
  pasos = 0;
  dato = "";

  return;
}

void calibrar_motor(bool Direction, EthernetClient client)
{
  dato = "";  
  encender_timer();
  digitalWrite(Dir, Direction);

  while (1)
  { 
    if (client)    
    {  
      while (client.connected())
      {
        if (client.available())
        {
          c = char(client.read());
          dato = dato + c;
        }
        
        if (c == '\n')
          break;
      }            
    }
    
    if (dato.charAt(0) == '3')
    {
      apagar_timer();
      dato = "";
      return;   
    }
    
    if (digitalRead(Switch) == HIGH || digitalRead(Switch2) == HIGH)
    {
      apagar_timer();      
      Direction = !Direction;
      digitalWrite(Dir, Direction);    
      encender_timer();
      
      while (1)
      {
        if (!(digitalRead(Switch) == HIGH || digitalRead(Switch2) == HIGH))
          break;
      }
      
      //Apagar el motor, desactivar y limpiar los timer
      apagar_timer();
      break;
    }    
  }

  //Comenzar a mover el deslizador desde alguno de los extremos
  //inicializar la variable de conteo de pasos de la interrupcion
  pasos_total = 0;
  //Configurar el timer con los mismos parametros y activar las
  //interrupciones
  encender_timer();
  digitalWrite(Dir, Direction);
  //Mover el motor hasta que haya llegado a alguno de los extremos
  while (1)
  {
    if (client)
    {
      while (client.connected())
      {
        if (client.available())
        {
          c = char(client.read());
          dato = dato + c;
        }
        
        if (c == '\n')
          break;
      }      
    }
    
    if (dato.charAt(0) == '3')
    {
      apagar_timer();
      dato = "";
      return;
    }
    
    if (digitalRead(Switch) == HIGH || digitalRead(Switch2) == HIGH)
    {
      //Apagar los timer, desactivar las interrupciones y apagar el motor
      //Repetir lo que se hizo en el caso anterior para que el deslizador
      //deje de chocar el interruptor      
      apagar_timer();      
      Direction = !Direction;
      digitalWrite(Dir, Direction);    
      encender_timer();
      
      while (1)
      {
        if (!(digitalRead(Switch) == HIGH || digitalRead(Switch2) == HIGH))
          break;
      }
      
      //Apagar el motor, desactivar y limpiar los timer
      apagar_timer();
      break;
    }    
  }
  //Guardar el tope de pasos que puede recorrer el deslizador (seguridad
  //por SW)
  pasos_tope = pasos_total;
  pasos_total = 0;
  dato = "";
  return;
}

void motor_inicio(EthernetClient client)
{   
  bool Direction = RIGHT;
  encender_timer();
  digitalWrite(Dir, Direction);
  //Mientras el pasos que haya contado la interrupcion sea menor 
  //a la distancia que se desea mover el deslizador, esperar
  while (1)
  { 
    if (client)
    {
      while (client.connected())
      {
        if (client.available())
        {
          c = char(client.read());
          dato = dato + c;
        }        
        if (c == '\n')
          break;
      }      
    }   

    if (dato.charAt(0) == '3')
    {
      apagar_timer();
      dato = "";
      return;
    }   

    if (digitalRead(Switch) == HIGH || digitalRead(Switch2) == HIGH)
    {
      apagar_timer();      
      Direction = !Direction;
      digitalWrite(Dir, Direction);    
      encender_timer();
      
      while (1)
      {
        if (digitalRead(Switch) == LOW && digitalRead(Switch2) == LOW)
          break;
      }
      apagar_timer();
      break;
    }
  }  
  pasos_total = 0;
  dato = "";
  return;
}

void encender_timer()
{
  noInterrupts();
  TCCR1A = 0;
  TCCR1B = 0;
  TCCR1A |= (1 << COM1A1 | 1 << COM1A0 | 1 << WGM11);
  TCCR1B |= (1 << WGM12 | 1 << WGM13);
  OCR1A = (1 - duty_cycle) * freq;
  ICR1 = freq;
  TCCR1B |= (1 << CS10);
  TIMSK1 |= (1 << OCIE1A);
  interrupts();
  //Activar las interrupciones y activar el movimiento del motor
  return;
}

void apagar_timer()
{
  TCCR1A = 0;
  TCCR1B = 0;
  TIMSK1 &= (0 << OCIE1A);
  noInterrupts();
  return;
}

ISR(TIMER1_COMPA_vect)
{
  pasos_total++;
}
