using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);
var dataPath = Environment.GetEnvironmentVariable("APPOINTMENTS_FILE")
    ?? Path.Combine(Environment.CurrentDirectory, "data", "appointments.json");
var store = new AppointmentStore(dataPath);
var app = builder.Build();

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));
app.MapGet("/appointments", (DateOnly? date) => Results.Ok(store.List(date)));
app.MapPost("/appointments", (CreateAppointmentRequest request) =>
{
    try
    {
        var appointment = store.Create(request);
        return Results.Created($"/appointments/{appointment.Id}", appointment);
    }
    catch (ArgumentException error)
    {
        return Results.BadRequest(new { error = error.Message });
    }
});
app.MapDelete("/appointments/{id:guid}", (Guid id) =>
    store.Cancel(id) ? Results.NoContent() : Results.NotFound());

app.Run();

public sealed record CreateAppointmentRequest(
    string PatientName,
    string Clinician,
    DateTimeOffset StartsAt,
    int DurationMinutes,
    string? Notes = null);

public sealed record Appointment(
    Guid Id,
    string PatientName,
    string Clinician,
    DateTimeOffset StartsAt,
    int DurationMinutes,
    string? Notes);

public sealed class AppointmentStore
{
    private static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };
    private readonly string _path;
    private readonly object _gate = new();
    private readonly List<Appointment> _appointments;

    public AppointmentStore(string path)
    {
        _path = Path.GetFullPath(path);
        _appointments = Load();
    }

    public IReadOnlyList<Appointment> List(DateOnly? date = null)
    {
        lock (_gate)
        {
            IEnumerable<Appointment> query = _appointments;
            if (date is not null)
            {
                query = query.Where(item => DateOnly.FromDateTime(item.StartsAt.UtcDateTime) == date.Value);
            }
            return query.OrderBy(item => item.StartsAt).ToArray();
        }
    }

    public Appointment Create(CreateAppointmentRequest request)
    {
        var patientName = request.PatientName?.Trim();
        var clinician = request.Clinician?.Trim();
        if (string.IsNullOrWhiteSpace(patientName) || patientName.Length > 120)
            throw new ArgumentException("PatientName must contain 1 to 120 characters.");
        if (string.IsNullOrWhiteSpace(clinician) || clinician.Length > 120)
            throw new ArgumentException("Clinician must contain 1 to 120 characters.");
        if (request.DurationMinutes is < 15 or > 240 || request.DurationMinutes % 15 != 0)
            throw new ArgumentException("DurationMinutes must be a 15-minute increment from 15 to 240.");
        if (request.StartsAt <= DateTimeOffset.UtcNow)
            throw new ArgumentException("StartsAt must be in the future.");
        if (request.Notes?.Length > 1000)
            throw new ArgumentException("Notes cannot exceed 1000 characters.");

        var startsAt = request.StartsAt.ToUniversalTime();
        var endsAt = startsAt.AddMinutes(request.DurationMinutes);
        lock (_gate)
        {
            var hasConflict = _appointments.Any(existing =>
                string.Equals(existing.Clinician, clinician, StringComparison.OrdinalIgnoreCase)
                && startsAt < existing.StartsAt.AddMinutes(existing.DurationMinutes)
                && existing.StartsAt < endsAt);
            if (hasConflict)
                throw new ArgumentException("This clinician already has an appointment during that time.");

            var appointment = new Appointment(
                Guid.NewGuid(), patientName, clinician, startsAt, request.DurationMinutes, request.Notes?.Trim());
            _appointments.Add(appointment);
            try
            {
                Save();
            }
            catch
            {
                _appointments.Remove(appointment);
                throw;
            }
            return appointment;
        }
    }

    public bool Cancel(Guid id)
    {
        lock (_gate)
        {
            var index = _appointments.FindIndex(item => item.Id == id);
            if (index < 0)
                return false;
            var removed = _appointments[index];
            _appointments.RemoveAt(index);
            try
            {
                Save();
            }
            catch
            {
                _appointments.Insert(index, removed);
                throw;
            }
            return true;
        }
    }

    private List<Appointment> Load()
    {
        if (!File.Exists(_path))
            return [];
        try
        {
            return JsonSerializer.Deserialize<List<Appointment>>(File.ReadAllText(_path)) ?? [];
        }
        catch (JsonException error)
        {
            throw new InvalidDataException($"Appointment data is invalid: {_path}", error);
        }
    }

    private void Save()
    {
        var directory = Path.GetDirectoryName(_path);
        if (!string.IsNullOrEmpty(directory))
            Directory.CreateDirectory(directory);
        var temporaryPath = $"{_path}.{Guid.NewGuid():N}.tmp";
        try
        {
            File.WriteAllText(temporaryPath, JsonSerializer.Serialize(_appointments, JsonOptions));
            File.Move(temporaryPath, _path, overwrite: true);
        }
        finally
        {
            if (File.Exists(temporaryPath))
                File.Delete(temporaryPath);
        }
    }
}
