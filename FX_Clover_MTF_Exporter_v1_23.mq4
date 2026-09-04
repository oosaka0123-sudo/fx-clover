#property strict
#property version   "1.23"
#property description "Exports closed GBPJPY D1/H4/H1/M15/M5 OHLC. No trading functions."

input int M5Bars = 100000;
input int M15Bars = 60000;
input int H1Bars = 20000;
input int H4Bars = 6000;
input int D1Bars = 2500;
input int TimerSeconds = 30;

datetime last_m5_closed_bar = 0;

int OnInit()
{
   EventSetTimer(MathMax(10, TimerSeconds));
   ExportAllClosedBars();
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason) { EventKillTimer(); }
void OnTick() { CheckForNewClosedM5Bar(); }
void OnTimer() { CheckForNewClosedM5Bar(); }

void CheckForNewClosedM5Bar()
{
   datetime closed_bar = iTime(Symbol(), PERIOD_M5, 1);
   if(closed_bar > 0 && closed_bar != last_m5_closed_bar)
      ExportAllClosedBars();
}

void ExportTimeframe(int timeframe, string filename, int requested_bars, string label)
{
   int available = iBars(Symbol(), timeframe);
   if(available <= 1)
   {
      Print("FX-Clover MTF exporter: no closed ", label, " bars available");
      return;
   }
   int count = MathMin(requested_bars, available - 1);
   int handle = FileOpen(filename, FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON, ',');
   if(handle == INVALID_HANDLE)
   {
      Print("FX-Clover MTF exporter FileOpen failed for ", label, ": ", GetLastError());
      return;
   }
   FileWrite(handle, "timestamp", "open", "high", "low", "close", "tick_volume");
   for(int shift = count; shift >= 1; shift--)
   {
      datetime t = iTime(Symbol(), timeframe, shift);
      if(t <= 0) continue;
      FileWrite(handle,
                TimeToString(t, TIME_DATE|TIME_MINUTES),
                DoubleToString(iOpen(Symbol(), timeframe, shift), Digits),
                DoubleToString(iHigh(Symbol(), timeframe, shift), Digits),
                DoubleToString(iLow(Symbol(), timeframe, shift), Digits),
                DoubleToString(iClose(Symbol(), timeframe, shift), Digits),
                IntegerToString((int)iVolume(Symbol(), timeframe, shift)));
   }
   FileFlush(handle);
   FileClose(handle);
   Print("FX-Clover MTF exporter wrote ", count, " closed ", label, " bars");
}

void ExportAllClosedBars()
{
   ExportTimeframe(PERIOD_M5,  "FX_Clover_GBPJPY_M5_closed.csv",  M5Bars,  "M5");
   ExportTimeframe(PERIOD_M15, "FX_Clover_GBPJPY_M15_closed.csv", M15Bars, "M15");
   ExportTimeframe(PERIOD_H1,  "FX_Clover_GBPJPY_H1_closed.csv",  H1Bars,  "H1");
   ExportTimeframe(PERIOD_H4,  "FX_Clover_GBPJPY_H4_closed.csv",  H4Bars,  "H4");
   ExportTimeframe(PERIOD_D1,  "FX_Clover_GBPJPY_D1_closed.csv",  D1Bars,  "D1");
   last_m5_closed_bar = iTime(Symbol(), PERIOD_M5, 1);
}

