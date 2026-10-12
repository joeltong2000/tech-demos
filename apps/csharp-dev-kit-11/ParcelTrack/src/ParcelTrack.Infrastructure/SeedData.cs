using ParcelTrack.Application;
using ParcelTrack.Domain;

namespace ParcelTrack.Infrastructure;

public static class SeedData
{
    public static void Populate(IParcelRepository repository)
    {
        var shipped = new Parcel("PT-1001", "Ada Lovelace", "London");
        shipped.RecordEvent(ParcelStatus.InTransit, "Rotterdam hub", "Departed origin");

        var delivered = new Parcel("PT-1002", "Grace Hopper", "Arlington");
        delivered.RecordEvent(ParcelStatus.InTransit, "Memphis hub");
        delivered.RecordEvent(ParcelStatus.OutForDelivery, "Arlington depot");
        delivered.RecordEvent(ParcelStatus.Delivered, "Front porch", "Signed by recipient");

        repository.Add(shipped);
        repository.Add(delivered);
        repository.Add(new Parcel("PT-1003", "Anders Hejlsberg", "Seattle"));
    }
}
