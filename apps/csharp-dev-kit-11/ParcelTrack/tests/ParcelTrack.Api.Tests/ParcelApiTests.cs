using System.Net;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc.Testing;
using ParcelTrack.Api;
using ParcelTrack.Domain;

namespace ParcelTrack.Api.Tests;

public class ParcelApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public ParcelApiTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetParcels_ReturnsSeededParcels()
    {
        var parcels = await _client.GetFromJsonAsync<List<ParcelResponse>>("/parcels");

        Assert.NotNull(parcels);
        Assert.Contains(parcels, p => p.Reference == "PT-1001");
        Assert.Contains(parcels, p => p.Reference == "PT-1002" && p.Status == ParcelStatus.Delivered);
    }

    [Fact]
    public async Task GetParcel_UnknownReference_Returns404()
    {
        var response = await _client.GetAsync("/parcels/PT-0000");

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task RegisterAndTrackParcel_HappyPath()
    {
        var created = await _client.PostAsJsonAsync(
            "/parcels",
            new RegisterParcelRequest("PT-2001", "Mads Torgersen", "Redmond"));
        Assert.Equal(HttpStatusCode.Created, created.StatusCode);

        var moved = await _client.PostAsJsonAsync(
            "/parcels/PT-2001/events",
            new RecordEventRequest(ParcelStatus.InTransit, "Oakland hub"));
        Assert.Equal(HttpStatusCode.OK, moved.StatusCode);

        var parcel = await _client.GetFromJsonAsync<ParcelResponse>("/parcels/PT-2001");
        Assert.NotNull(parcel);
        Assert.Equal(ParcelStatus.InTransit, parcel.Status);
        Assert.Equal(2, parcel.Events.Count);
    }

    [Fact]
    public async Task RegisterDuplicate_Returns409()
    {
        var request = new RegisterParcelRequest("PT-2002", "Scott Hanselman", "Portland");
        await _client.PostAsJsonAsync("/parcels", request);

        var duplicate = await _client.PostAsJsonAsync("/parcels", request);

        Assert.Equal(HttpStatusCode.Conflict, duplicate.StatusCode);
    }

    [Fact]
    public async Task InvalidTransition_Returns422()
    {
        await _client.PostAsJsonAsync(
            "/parcels",
            new RegisterParcelRequest("PT-2003", "Dustin Campbell", "Nashville"));

        var response = await _client.PostAsJsonAsync(
            "/parcels/PT-2003/events",
            new RecordEventRequest(ParcelStatus.Delivered, "Doorstep"));

        Assert.Equal(HttpStatusCode.UnprocessableContent, response.StatusCode);
    }
}
