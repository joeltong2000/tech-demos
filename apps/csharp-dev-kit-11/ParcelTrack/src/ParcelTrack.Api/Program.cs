using ParcelTrack.Api;
using ParcelTrack.Application;
using ParcelTrack.Domain;
using ParcelTrack.Infrastructure;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddSingleton<IParcelRepository>(_ =>
{
    var repository = new InMemoryParcelRepository();
    SeedData.Populate(repository);
    return repository;
});
builder.Services.AddSingleton<ParcelService>();

var app = builder.Build();

app.MapGet("/parcels", (ParcelService service) =>
    Results.Ok(service.All().Select(ParcelResponse.From)));

app.MapGet("/parcels/{reference}", (string reference, ParcelService service) =>
    service.Find(reference) is { } parcel
        ? Results.Ok(ParcelResponse.From(parcel))
        : Results.NotFound(new { error = $"No parcel '{reference}'." }));

app.MapPost("/parcels", (RegisterParcelRequest request, ParcelService service) =>
{
    try
    {
        var parcel = service.Register(request.Reference, request.Recipient, request.Destination);
        return Results.Created($"/parcels/{parcel.Reference}", ParcelResponse.From(parcel));
    }
    catch (DuplicateParcelException ex)
    {
        return Results.Conflict(new { error = ex.Message });
    }
    catch (ArgumentException ex)
    {
        return Results.BadRequest(new { error = ex.Message });
    }
});

app.MapPost("/parcels/{reference}/events", (string reference, RecordEventRequest request, ParcelService service) =>
{
    try
    {
        var trackingEvent = service.RecordEvent(reference, request.Status, request.Location, request.Note);
        return Results.Ok(trackingEvent);
    }
    catch (ParcelNotFoundException ex)
    {
        return Results.NotFound(new { error = ex.Message });
    }
    catch (InvalidStatusTransitionException ex)
    {
        return Results.UnprocessableEntity(new { error = ex.Message });
    }
});

app.Run();

public partial class Program;
