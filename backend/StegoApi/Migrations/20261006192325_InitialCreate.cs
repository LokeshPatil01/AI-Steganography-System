using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace StegoApi.Migrations
{
    /// <inheritdoc />
    public partial class InitialCreate : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Users",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uniqueidentifier", nullable: false),
                    Username = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: false),
                    Email = table.Column<string>(type: "nvarchar(256)", maxLength: 256, nullable: false),
                    PasswordHash = table.Column<string>(type: "nvarchar(512)", maxLength: 512, nullable: false),
                    PasswordSalt = table.Column<string>(type: "nvarchar(256)", maxLength: 256, nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "datetime2", nullable: false, defaultValueSql: "GETUTCDATE()"),
                    IsActive = table.Column<bool>(type: "bit", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Users", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "StegoOperations",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uniqueidentifier", nullable: false),
                    UserId = table.Column<Guid>(type: "uniqueidentifier", nullable: false),
                    OperationType = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: false),
                    CoverImageHash = table.Column<string>(type: "nvarchar(64)", maxLength: 64, nullable: false),
                    StegoImageHash = table.Column<string>(type: "nvarchar(64)", maxLength: 64, nullable: false),
                    PayloadSizeBytes = table.Column<long>(type: "bigint", nullable: false),
                    SecurityLevel = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: false),
                    DetectabilityScore = table.Column<double>(type: "float", nullable: true),
                    PsnrDb = table.Column<double>(type: "float", nullable: true),
                    Ssim = table.Column<double>(type: "float", nullable: true),
                    Mse = table.Column<double>(type: "float", nullable: true),
                    ExecutionTimeMs = table.Column<long>(type: "bigint", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "datetime2", nullable: false, defaultValueSql: "GETUTCDATE()")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_StegoOperations", x => x.Id);
                    table.ForeignKey(
                        name: "FK_StegoOperations_Users_UserId",
                        column: x => x.UserId,
                        principalTable: "Users",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "UserKeys",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uniqueidentifier", nullable: false),
                    UserId = table.Column<Guid>(type: "uniqueidentifier", nullable: false),
                    PublicKeyPem = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    EncryptedPrivateKeyPem = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    KeyIv = table.Column<string>(type: "nvarchar(64)", maxLength: 64, nullable: false),
                    KeyTag = table.Column<string>(type: "nvarchar(64)", maxLength: 64, nullable: false),
                    KeyFingerprint = table.Column<string>(type: "nvarchar(64)", maxLength: 64, nullable: false),
                    KeySizeBits = table.Column<int>(type: "int", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "datetime2", nullable: false, defaultValueSql: "GETUTCDATE()"),
                    IsRevoked = table.Column<bool>(type: "bit", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UserKeys", x => x.Id);
                    table.ForeignKey(
                        name: "FK_UserKeys_Users_UserId",
                        column: x => x.UserId,
                        principalTable: "Users",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_StegoOperations_CoverImageHash",
                table: "StegoOperations",
                column: "CoverImageHash");

            migrationBuilder.CreateIndex(
                name: "IX_StegoOperations_StegoImageHash",
                table: "StegoOperations",
                column: "StegoImageHash");

            migrationBuilder.CreateIndex(
                name: "IX_StegoOperations_UserId_CreatedAt",
                table: "StegoOperations",
                columns: new[] { "UserId", "CreatedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_UserKeys_KeyFingerprint",
                table: "UserKeys",
                column: "KeyFingerprint");

            migrationBuilder.CreateIndex(
                name: "IX_UserKeys_UserId_IsRevoked",
                table: "UserKeys",
                columns: new[] { "UserId", "IsRevoked" });

            migrationBuilder.CreateIndex(
                name: "IX_Users_Email",
                table: "Users",
                column: "Email",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Users_Username",
                table: "Users",
                column: "Username",
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "StegoOperations");

            migrationBuilder.DropTable(
                name: "UserKeys");

            migrationBuilder.DropTable(
                name: "Users");
        }
    }
}
