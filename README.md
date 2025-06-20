# 🛰️ SignalSlice

**SignalSlice** is an OSINT-inspired alert system that tracks spikes in late-night pizza ordering near the Pentagon — known colloquially as the "Pentagon Pizza Index" — to signal potential high-level activity. When an unusual spike is detected, users receive instant notifications via TBD

The motivation for this project comes from the legendary Pentagon Piza Index, where it has accurately predicted 38 disasters (ranging from natural disasters to war). When the Pentagon orders pizza late at night, it typically means staff are required to stay late and work on something important, likely of national importance.

---

## 📦 Project Summary

> 🍕 "Where there’s smoke, there’s fire. Where there’s pizza, there’s a meeting."

This project blends humor with open-source intelligence principles to monitor real-time or simulated pizza order data. By analyzing trends and alerting users to anomalies, SignalSlice offers a lighthearted but insightful window into late-night activity that could signal something bigger.

---

## 🚀 Features

- 📊 **Live Pizza Index Monitoring** – Tracks order spikes near the Pentagon (real or simulated data).
- ⚠️ **Threshold-based Alerts** – Notifies users when activity exceeds rolling averages.
- 📨 **Multi-Channel Notifications** – Supports Email, SMS (Twilio), and Discord/Webhook (MAYBE) alerts.
- 🧠 **Smart Spike Detection** – Uses moving average and standard deviation to flag anomalies.
- 📈 **Dashboard (optional)** – View historical index trends and configure alert thresholds.

---

## 📡 How It Works

1. The system polls multiple data sources every 15-30 minutes. Webscraping is used to gather large amounts of data.
2. It calculates the current "Pizza Index" using a rolling average model.
3. If the current order volume exceeds a configurable threshold (defined by training with similar days -- weekday? holiday? summer? tourist?), it triggers an alert.
4. Alerts are dispatched to subscribed users via their selected notification method(s).

---

## 📥 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/signalslice.git
cd signalslice
