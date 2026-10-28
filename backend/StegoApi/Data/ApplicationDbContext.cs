using Microsoft.EntityFrameworkCore;
using StegoApi.Models.Entities;

namespace StegoApi.Data;

public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    public DbSet<User> Users => Set<User>();
    public DbSet<UserKey> UserKeys => Set<UserKey>();
    public DbSet<StegoOperation> StegoOperations => Set<StegoOperation>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // User Configuration
        modelBuilder.Entity<User>(entity =>
        {
            entity.HasKey(u => u.Id);

            entity.HasIndex(u => u.Email)
                  .IsUnique()
                  .HasDatabaseName("IX_Users_Email");

            entity.HasIndex(u => u.Username)
                  .IsUnique()
                  .HasDatabaseName("IX_Users_Username");

            entity.Property(u => u.CreatedAt)
                  .HasDefaultValueSql("GETUTCDATE()");
        });

        // UserKey Configuration
        modelBuilder.Entity<UserKey>(entity =>
        {
            entity.HasKey(k => k.Id);

            entity.HasOne(k => k.User)
                  .WithMany(u => u.Keys)
                  .HasForeignKey(k => k.UserId)
                  .OnDelete(DeleteBehavior.Cascade);

            entity.HasIndex(k => new { k.UserId, k.IsRevoked })
                  .HasDatabaseName("IX_UserKeys_UserId_IsRevoked");

            entity.HasIndex(k => k.KeyFingerprint)
                  .HasDatabaseName("IX_UserKeys_KeyFingerprint");

            entity.Property(k => k.CreatedAt)
                  .HasDefaultValueSql("GETUTCDATE()");
        });

        // StegoOperation Configuration
        modelBuilder.Entity<StegoOperation>(entity =>
        {
            entity.HasKey(o => o.Id);

            entity.HasOne(o => o.User)
                  .WithMany(u => u.Operations)
                  .HasForeignKey(o => o.UserId)
                  .OnDelete(DeleteBehavior.Cascade);

            entity.HasIndex(o => new { o.UserId, o.CreatedAt })
                  .HasDatabaseName("IX_StegoOperations_UserId_CreatedAt");

            entity.HasIndex(o => o.CoverImageHash)
                  .HasDatabaseName("IX_StegoOperations_CoverImageHash");

            entity.HasIndex(o => o.StegoImageHash)
                  .HasDatabaseName("IX_StegoOperations_StegoImageHash");

            entity.Property(o => o.CreatedAt)
                  .HasDefaultValueSql("GETUTCDATE()");
        });
    }
}
