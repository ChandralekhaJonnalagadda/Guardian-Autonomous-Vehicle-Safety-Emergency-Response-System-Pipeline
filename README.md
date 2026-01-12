# Guardian

## Autonomous Vehicle Safety & Emergency Response System

---

## 📌 Project Overview

Guardian was built to address a critical gap in emergency response systems — accidents that occur on isolated or low-traffic roads where there are no bystanders, no CCTV coverage, and victims may be unconscious or unable to call for help.

The project focuses on **real-time accident detection**, **false-alarm reduction**, and **autonomous emergency escalation** using a cloud-native, event-driven architecture on AWS. Guardian demonstrates how high-velocity telemetry, sensor fusion, and stateful decision-making can be combined to build **reliable, life-critical systems**.

---

## ⚙️ System Overview

Guardian is designed for the **Golden Hour** of emergency response — the narrow window where rapid action can determine survival outcomes. The system transforms raw sensor signals into a **digital representation of a crash event**, allowing emergency decisions to be made automatically.

Key system characteristics:

* Real-time ingestion of vehicle telemetry via Amazon Kinesis
* Sensor fusion–based severity classification
* Stateful incident tracking using DynamoDB
* Autonomous escalation for non-responsive occupants

---

## 🚗 How Real-Time Data Is Collected (On-Device Logic)

For this project, real-time telemetry is **simulated using a Python generator function** that emits realistic sensor events (normal driving, near-miss, and crash scenarios). This allows controlled testing of streaming, triage, and escalation logic without physical hardware.

In a production environment, this generator would be replaced by **IoT-based ingestion using MQTT**, where each vehicle or mobile device publishes telemetry directly to the cloud.

### On-Device Behavior (Conceptual)

* A lightweight agent runs locally on the vehicle system or companion mobile app
* Under normal driving conditions, only low-frequency heartbeat signals are sent
* High speed alone does not trigger alerts (low G-force)
* When a **sudden extreme G-force spike** is detected, the device immediately publishes a high-priority telemetry burst

This event-driven burst model minimizes noise, reduces cost, and ensures critical incidents reach the system instantly.

---

## 🏗️ End-to-End Data Architecture

### 1️⃣ Ingestion Layer (The Data Highway)

Telemetry events are ingested using **Amazon Kinesis Data Streams**, providing ordered, scalable, and low-latency ingestion for high-impact events.

#### Telemetry Schema

* `vin` – Unique vehicle identifier (Partition Key)
* `g_force` – Impact magnitude (primary trigger)
* `heartbeat` – Occupant pulse (1 = pulse detected, 0 = no pulse)
* `tilt_angle` – Gyroscopic reading for rollover detection
* `airbag_deployed` – Boolean signal from vehicle SRS module
* `speed` – Velocity at impact
* `scenario_type` – Context (NORMAL, CRASH_CONSCIOUS, CRASH_UNCONSCIOUS)
* `timestamp` – ISO-8601 high-precision timestamp

---

### 2️⃣ Sensor Fusion & Stateful Triage (The Brain)

Guardian uses **multi-signal confirmation** rather than relying on a single sensor. This dramatically reduces false positives from potholes, sudden braking, or near-miss incidents.

#### Priority-Based Triage Rules

**Priority 1 – Instant Escalation (Code Red)**

* `airbag_deployed == TRUE` OR `tilt_angle > 60°`
* Immediate emergency escalation (no timers)

**Priority 2 – Unconscious Occupant**

* `g_force > 8.0` AND `heartbeat == 0`
* Immediate Code Red escalation

**Priority 3 – Interactive Warning Flow (False Alarm Protection)**

* `g_force > 8.0` AND `heartbeat == 1`

This flow exists to handle real-world edge cases such as:

* Sudden emergency braking
* Near-miss collisions
* Minor impacts with no injuries

Instead of escalating immediately:

* The incident enters a `WARNING` state
* A **15-second safety window** is written to DynamoDB
* The user is asked to confirm whether they are safe

If the user dismisses the alert, the incident is marked **RESOLVED**. If no response is received within the window, the system escalates automatically.

---

## 🛡️ Fail-Safe Sticky State Logic

Guardian enforces **state locking** to prevent accidental clearance of emergencies.

* Once an incident enters `WARNING` or `ESCALATED`
* Subsequent `NORMAL` telemetry is ignored
* Only an explicit user dismissal can clear the state

This guarantees deterministic behavior during life-critical scenarios.

---

## ⏱️ Autonomous Watchdog Protocol

Guardian treats **silence as a signal**.

Using **Amazon EventBridge**, a scheduled watchdog process runs every 60 seconds and scans DynamoDB for expired warning windows. Any unacknowledged warnings are automatically upgraded to `ESCALATED`, ensuring help is dispatched even if the occupant becomes incapacitated after the initial alert.

---

## 📣 Notification Layer

* **Amazon API Gateway** provides a secure endpoint for users to dismiss false alarms
* **Amazon SNS** orchestrates emergency notifications

### SMS Constraint & Design Choice

Due to global regulatory changes (10DLC and Toll-Free requirements), SMS delivery requires Origination Identity registration and carrier approval.

**MVP Decision:** High-priority SNS Email alerts were used to ensure 100% delivery reliability without regulatory delays.

---

## ☁️ AWS Services Used

* Amazon Kinesis Data Streams
* AWS Lambda
* Amazon DynamoDB
* Amazon EventBridge
* Amazon API Gateway
* Amazon SNS
* Amazon S3

---

## 🚀 Future Roadmap

### 🔹 AWS IoT Core & Edge Processing

* Migrate ingestion to AWS IoT Core (MQTT)
* Filter 99% of normal telemetry at the edge
* Reduce cloud ingestion costs by ~70%

### 🔹 Geospatial Intelligence

* Embed GPS coordinates in alerts
* Generate Google Maps deep links
* Identify accident hotspots on isolated routes

### 🔹 Streaming Analytics & Warehousing

* Persist events to Amazon S3
* Use Databricks for large-scale streaming analytics
* Use Snowflake for historical reporting and BI dashboards

### 🔹 Predictive Safety (SageMaker)

* Predict hidden structural damage
* Identify high-risk driving patterns
* Enable proactive vehicle maintenance

---

## ⭐ Why Guardian Stands Out

* Real-time, event-driven architecture
* Sensor fusion–based triage
* Stateful, autonomous escalation logic
* Designed for infrastructure-less environments
* Mirrors real-world emergency response platforms

---

## 🎯 Outcome

Guardian proves that cloud-native data engineering can go beyond analytics — enabling **autonomous, life-saving decision systems** where every second matters.
