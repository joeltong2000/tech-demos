using ParcelTrack.Domain;

namespace ParcelTrack.Domain.Tests;

public class ParcelTests
{
    [Fact]
    public void NewParcel_StartsRegistered_WithOneEvent()
    {
        var parcel = new Parcel("pt-9000", "Test Recipient", "Testville");

        Assert.Equal("PT-9000", parcel.Reference);
        Assert.Equal(ParcelStatus.Registered, parcel.Status);
        Assert.Single(parcel.Events);
    }

    [Theory]
    [InlineData("")]
    [InlineData("   ")]
    public void NewParcel_RejectsBlankReference(string reference)
    {
        Assert.Throws<ArgumentException>(() => new Parcel(reference, "Someone", "Somewhere"));
    }

    [Fact]
    public void RecordEvent_FollowsHappyPath_ToDelivered()
    {
        var parcel = new Parcel("PT-9001", "Test Recipient", "Testville");

        parcel.RecordEvent(ParcelStatus.InTransit, "Hub A");
        parcel.RecordEvent(ParcelStatus.OutForDelivery, "Local depot");
        parcel.RecordEvent(ParcelStatus.Delivered, "Doorstep", "Left with neighbour");

        Assert.Equal(ParcelStatus.Delivered, parcel.Status);
        Assert.Equal(4, parcel.Events.Count);
        Assert.Equal("Left with neighbour", parcel.Events[^1].Note);
    }

    [Fact]
    public void RecordEvent_RejectsSkippingStraightToDelivered()
    {
        var parcel = new Parcel("PT-9002", "Test Recipient", "Testville");

        var ex = Assert.Throws<InvalidStatusTransitionException>(
            () => parcel.RecordEvent(ParcelStatus.Delivered, "Doorstep"));

        Assert.Equal(ParcelStatus.Registered, ex.From);
        Assert.Equal(ParcelStatus.Delivered, ex.To);
        Assert.Equal(ParcelStatus.Registered, parcel.Status);
    }

    [Fact]
    public void RecordEvent_RejectsLeavingTerminalStates()
    {
        var parcel = new Parcel("PT-9003", "Test Recipient", "Testville");
        parcel.RecordEvent(ParcelStatus.InTransit, "Hub A");
        parcel.RecordEvent(ParcelStatus.ReturnedToSender, "Hub A", "Address unknown");

        Assert.Throws<InvalidStatusTransitionException>(
            () => parcel.RecordEvent(ParcelStatus.InTransit, "Hub B"));
    }

    [Theory]
    [InlineData(ParcelStatus.Registered, ParcelStatus.InTransit, true)]
    [InlineData(ParcelStatus.Registered, ParcelStatus.OutForDelivery, false)]
    [InlineData(ParcelStatus.InTransit, ParcelStatus.InTransit, true)]
    [InlineData(ParcelStatus.OutForDelivery, ParcelStatus.InTransit, true)]
    [InlineData(ParcelStatus.Delivered, ParcelStatus.InTransit, false)]
    public void IsValidTransition_MatchesStateMachine(ParcelStatus from, ParcelStatus to, bool expected)
    {
        Assert.Equal(expected, Parcel.IsValidTransition(from, to));
    }
}
