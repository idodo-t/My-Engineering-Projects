# Medical Appointment Booking API

I built a .NET 9 minimal API for creating, listing, and cancelling medical appointments. It persists appointments as JSON, validates request fields, and prevents overlapping bookings for the same clinician.

## Run

Requires the .NET 9 SDK.

```bash
dotnet run --project MedicalAppointments.csproj --urls http://127.0.0.1:5087
```

The API listens on localhost by default when using the command above. Data is stored in `data/appointments.json`; set `APPOINTMENTS_FILE` to choose another path.

## Endpoints

- `GET /health` checks service status.
- `GET /appointments` lists appointments; optional `?date=YYYY-MM-DD` filters by UTC date.
- `POST /appointments` creates an appointment from JSON fields `patientName`, `clinician`, `startsAt`, `durationMinutes`, and optional `notes`.
- `DELETE /appointments/{id}` cancels an appointment.

Durations must be 15-minute increments from 15 to 240 minutes. Appointment times must be in the future, and a clinician cannot have overlapping appointments. This is a local demo API, not a production medical system: it has no authentication, authorization, encryption, or clinical data protections. Do not expose it publicly or submit real patient information.
