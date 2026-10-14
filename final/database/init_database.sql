-- ============================================================================
-- HỆ THỐNG CƠ SỞ DỮ LIỆU THƯƠNG MẠI & QUẢN LÝ DỊCH VỤ KHÁCH HÀNG (NARRAI PLATFORM)
-- RDBMS: Microsoft SQL Server (2019 / 2022 / 2025)
-- Database Name: NarrAI_CommerceDB
-- ============================================================================

USE master;
GO

-- 1. TẠO DATABASE NẾU CHƯA TỒN TẠI
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'NarrAI_CommerceDB')
BEGIN
    CREATE DATABASE NarrAI_CommerceDB
    COLLATE Vietnamese_CI_AS;
    PRINT N'==> Đã tạo thành công Database [NarrAI_CommerceDB].';
END
ELSE
BEGIN
    PRINT N'==> Database [NarrAI_CommerceDB] đã tồn tại sẵn.';
END
GO

USE NarrAI_CommerceDB;
GO

-- ============================================================================
-- 2. TẠO CÁC BẢNG QUẢN LÝ THÔNG TIN KHÁCH HÀNG, SẢN PHẨM, HÓA ĐƠN & DỊCH VỤ
-- ============================================================================

-- 2.1 BẢNG KHÁCH HÀNG (CUSTOMERS / USERS)
IF OBJECT_ID(N'dbo.Customers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Customers (
        CustomerID INT IDENTITY(1,1) PRIMARY KEY,
        CustomerCode NVARCHAR(50) NOT NULL UNIQUE,
        Username NVARCHAR(100) NOT NULL UNIQUE,
        PasswordHash NVARCHAR(255) NOT NULL,
        FullName NVARCHAR(150) NOT NULL,
        Email NVARCHAR(150) NOT NULL UNIQUE,
        PhoneNumber NVARCHAR(20) NULL,
        Address NVARCHAR(255) NULL,
        City NVARCHAR(100) NULL,
        CoinBalance INT NOT NULL DEFAULT 0 CONSTRAINT CHK_Customer_CoinBalance CHECK (CoinBalance >= 0),
        AvatarUrl NVARCHAR(500) NULL,
        CustomerTier NVARCHAR(50) NOT NULL DEFAULT N'Standard' CONSTRAINT CHK_Customer_Tier CHECK (CustomerTier IN (N'Standard', N'VIP', N'Pro_Author', N'Enterprise')),
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2(3) NOT NULL DEFAULT GETDATE(),
        UpdatedAt DATETIME2(3) NOT NULL DEFAULT GETDATE()
    );
    PRINT N'==> Đã tạo bảng [Customers] (Thông tin khách hàng).';
END
GO

-- 2.2 BẢNG DANH MỤC SẢN PHẨM / GÓI DỊCH VỤ (PRODUCT CATEGORIES)
IF OBJECT_ID(N'dbo.ProductCategories', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ProductCategories (
        CategoryID INT IDENTITY(1,1) PRIMARY KEY,
        CategoryCode NVARCHAR(50) NOT NULL UNIQUE,
        CategoryName NVARCHAR(100) NOT NULL,
        Description NVARCHAR(255) NULL,
        DisplayOrder INT NOT NULL DEFAULT 1,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2(3) NOT NULL DEFAULT GETDATE()
    );
    PRINT N'==> Đã tạo bảng [ProductCategories] (Danh mục sản phẩm/dịch vụ).';
END
GO

-- 2.3 BẢNG SẢN PHẨM & GÓI DỊCH VỤ (PRODUCTS & SERVICES)
IF OBJECT_ID(N'dbo.Products', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Products (
        ProductID INT IDENTITY(1,1) PRIMARY KEY,
        CategoryID INT NOT NULL CONSTRAINT FK_Products_Category FOREIGN KEY REFERENCES dbo.ProductCategories(CategoryID),
        ProductCode NVARCHAR(50) NOT NULL UNIQUE,
        ProductName NVARCHAR(150) NOT NULL,
        Description NVARCHAR(MAX) NULL,
        PriceVND DECIMAL(18, 2) NOT NULL DEFAULT 0 CONSTRAINT CHK_Product_Price CHECK (PriceVND >= 0),
        CoinsReward INT NOT NULL DEFAULT 0,              -- Số xu nạp cộng vào tài khoản
        DurationDays INT NOT NULL DEFAULT 0,             -- Số ngày hiệu lực (0 = nạp xu vĩnh viễn)
        MaxComicGenerations INT NOT NULL DEFAULT 0,      -- Số lượt tạo truyện tranh kèm theo
        ThumbnailUrl NVARCHAR(500) NULL,
        IsHotPromo BIT NOT NULL DEFAULT 0,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2(3) NOT NULL DEFAULT GETDATE(),
        UpdatedAt DATETIME2(3) NOT NULL DEFAULT GETDATE()
    );
    PRINT N'==> Đã tạo bảng [Products] (Sản phẩm & Gói dịch vụ).';
END
GO

-- 2.4 BẢNG HÓA ĐƠN & GIAO DỊCH THANH TOÁN (INVOICES / ORDERS)
IF OBJECT_ID(N'dbo.Invoices', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Invoices (
        InvoiceID INT IDENTITY(1,1) PRIMARY KEY,
        InvoiceNumber NVARCHAR(50) NOT NULL UNIQUE,      -- VD: INV-20261011-0001
        CustomerID INT NOT NULL CONSTRAINT FK_Invoices_Customer FOREIGN KEY REFERENCES dbo.Customers(CustomerID),
        SubtotalVND DECIMAL(18, 2) NOT NULL DEFAULT 0,
        DiscountVND DECIMAL(18, 2) NOT NULL DEFAULT 0,
        TaxVND DECIMAL(18, 2) NOT NULL DEFAULT 0,
        TotalAmountVND DECIMAL(18, 2) NOT NULL DEFAULT 0 CONSTRAINT CHK_Invoice_Total CHECK (TotalAmountVND >= 0),
        PaymentMethod NVARCHAR(50) NOT NULL DEFAULT N'VNPAY' CONSTRAINT CHK_Invoice_PaymentMethod CHECK (PaymentMethod IN (N'VNPAY', N'MOMO', N'BANK_TRANSFER', N'ZALOPAY', N'CREDIT_CARD', N'MANUAL_ADMIN')),
        PaymentStatus NVARCHAR(50) NOT NULL DEFAULT N'PENDING' CONSTRAINT CHK_Invoice_PaymentStatus CHECK (PaymentStatus IN (N'PENDING', N'PAID', N'CANCELLED', N'REFUNDED', N'FAILED')),
        TransactionReference NVARCHAR(100) NULL,         -- Mã giao dịch từ cổng VNPAY/MOMO/Ngân hàng
        PaidAt DATETIME2(3) NULL,
        CustomerNotes NVARCHAR(500) NULL,
        AdminNotes NVARCHAR(500) NULL,
        CreatedAt DATETIME2(3) NOT NULL DEFAULT GETDATE(),
        UpdatedAt DATETIME2(3) NOT NULL DEFAULT GETDATE()
    );
    PRINT N'==> Đã tạo bảng [Invoices] (Hóa đơn thanh toán).';
END
GO

-- 2.5 BẢNG CHI TIẾT HÓA ĐƠN (INVOICE DETAILS / LINE ITEMS)
IF OBJECT_ID(N'dbo.InvoiceDetails', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.InvoiceDetails (
        DetailID INT IDENTITY(1,1) PRIMARY KEY,
        InvoiceID INT NOT NULL CONSTRAINT FK_InvoiceDetails_Invoice FOREIGN KEY REFERENCES dbo.Invoices(InvoiceID) ON DELETE CASCADE,
        ProductID INT NOT NULL CONSTRAINT FK_InvoiceDetails_Product FOREIGN KEY REFERENCES dbo.Products(ProductID),
        Quantity INT NOT NULL DEFAULT 1 CONSTRAINT CHK_Detail_Quantity CHECK (Quantity > 0),
        UnitPriceVND DECIMAL(18, 2) NOT NULL DEFAULT 0,
        CoinsPerUnit INT NOT NULL DEFAULT 0,
        LineTotalVND DECIMAL(18, 2) NOT NULL DEFAULT 0,
        CreatedAt DATETIME2(3) NOT NULL DEFAULT GETDATE()
    );
    PRINT N'==> Đã tạo bảng [InvoiceDetails] (Chi tiết hóa đơn).';
END
GO

-- 2.6 BẢNG DỊCH VỤ & GÓI HỘI VIÊN KHÁCH HÀNG ĐANG SỞ HỮU (CUSTOMER SERVICES & SUBSCRIPTIONS)
IF OBJECT_ID(N'dbo.CustomerServices', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CustomerServices (
        SubscriptionID INT IDENTITY(1,1) PRIMARY KEY,
        CustomerID INT NOT NULL CONSTRAINT FK_CustomerServices_Customer FOREIGN KEY REFERENCES dbo.Customers(CustomerID),
        ProductID INT NOT NULL CONSTRAINT FK_CustomerServices_Product FOREIGN KEY REFERENCES dbo.Products(ProductID),
        InvoiceID INT NULL CONSTRAINT FK_CustomerServices_Invoice FOREIGN KEY REFERENCES dbo.Invoices(InvoiceID),
        ServiceName NVARCHAR(150) NOT NULL,
        StartDate DATETIME2(3) NOT NULL DEFAULT GETDATE(),
        EndDate DATETIME2(3) NULL,                       -- NULL = Gói vĩnh viễn (gói nạp xu)
        Status NVARCHAR(50) NOT NULL DEFAULT N'ACTIVE' CONSTRAINT CHK_Service_Status CHECK (Status IN (N'ACTIVE', N'EXPIRED', N'CANCELLED', N'SUSPENDED')),
        RemainingComicGenerations INT NOT NULL DEFAULT 0,
        AutoRenew BIT NOT NULL DEFAULT 0,
        CreatedAt DATETIME2(3) NOT NULL DEFAULT GETDATE(),
        UpdatedAt DATETIME2(3) NOT NULL DEFAULT GETDATE()
    );
    PRINT N'==> Đã tạo bảng [CustomerServices] (Dịch vụ & Gói sở hữu của khách hàng).';
END
GO

-- 2.7 BẢNG NHẬT KÝ SỬ DỤNG DỊCH VỤ & BIẾN ĐỘNG SỐ DƯ XU (COIN & SERVICE TRANSACTION LOGS)
IF OBJECT_ID(N'dbo.CoinTransactionLogs', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CoinTransactionLogs (
        LogID INT IDENTITY(1,1) PRIMARY KEY,
        CustomerID INT NOT NULL CONSTRAINT FK_CoinLogs_Customer FOREIGN KEY REFERENCES dbo.Customers(CustomerID),
        ActionType NVARCHAR(50) NOT NULL CONSTRAINT CHK_Coin_ActionType CHECK (ActionType IN (N'TOPUP', N'COMIC_GENERATE', N'STORY_GENERATE', N'STORY_EDIT', N'REFUND', N'PROMO_GIFT')),
        AmountCoins INT NOT NULL,                        -- Số dương nếu nạp, số âm nếu tiêu xu
        BalanceBefore INT NOT NULL,
        BalanceAfter INT NOT NULL,
        ReferenceID NVARCHAR(100) NULL,                  -- story_id, comic_id hoặc invoice_number
        Description NVARCHAR(500) NOT NULL,
        CreatedAt DATETIME2(3) NOT NULL DEFAULT GETDATE()
    );
    PRINT N'==> Đã tạo bảng [CoinTransactionLogs] (Nhật ký tiêu xu & sử dụng dịch vụ).';
END
GO

-- 2.8 BẢNG YÊU CẦU HỖ TRỢ / CHĂM SÓC KHÁCH HÀNG (CUSTOMER SUPPORT TICKETS)
IF OBJECT_ID(N'dbo.CustomerSupportTickets', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CustomerSupportTickets (
        TicketID INT IDENTITY(1,1) PRIMARY KEY,
        TicketCode NVARCHAR(50) NOT NULL UNIQUE,
        CustomerID INT NOT NULL CONSTRAINT FK_Tickets_Customer FOREIGN KEY REFERENCES dbo.Customers(CustomerID),
        Subject NVARCHAR(200) NOT NULL,
        Category NVARCHAR(50) NOT NULL DEFAULT N'PAYMENT_ISSUE' CONSTRAINT CHK_Ticket_Category CHECK (Category IN (N'PAYMENT_ISSUE', N'COMIC_RENDER_ISSUE', N'STORY_AI_ISSUE', N'ACCOUNT_SECURITY', N'OTHER')),
        Priority NVARCHAR(20) NOT NULL DEFAULT N'MEDIUM' CONSTRAINT CHK_Ticket_Priority CHECK (Priority IN (N'LOW', N'MEDIUM', N'HIGH', N'URGENT')),
        Status NVARCHAR(30) NOT NULL DEFAULT N'OPEN' CONSTRAINT CHK_Ticket_Status CHECK (Status IN (N'OPEN', N'IN_PROGRESS', N'RESOLVED', N'CLOSED')),
        CustomerMessage NVARCHAR(MAX) NOT NULL,
        AdminResponse NVARCHAR(MAX) NULL,
        CreatedAt DATETIME2(3) NOT NULL DEFAULT GETDATE(),
        ResolvedAt DATETIME2(3) NULL
    );
    PRINT N'==> Đã tạo bảng [CustomerSupportTickets] (Yêu cầu hỗ trợ khách hàng).';
END
GO

-- ============================================================================
-- 3. TẠO CÁC INDEXES TỐI ƯU HÓA TRUY VẤN
-- ============================================================================
CREATE NONCLUSTERED INDEX IX_Invoices_Customer ON dbo.Invoices(CustomerID, PaymentStatus, CreatedAt DESC);
CREATE NONCLUSTERED INDEX IX_Invoices_InvoiceNumber ON dbo.Invoices(InvoiceNumber);
CREATE NONCLUSTERED INDEX IX_CustomerServices_Customer ON dbo.CustomerServices(CustomerID, Status, EndDate);
CREATE NONCLUSTERED INDEX IX_CoinLogs_Customer_Date ON dbo.CoinTransactionLogs(CustomerID, CreatedAt DESC);
CREATE NONCLUSTERED INDEX IX_Products_Category ON dbo.Products(CategoryID, IsActive);
GO

-- ============================================================================
-- 4. TẠO CÁC VIEW BÁO CÁO THỐNG KÊ (ANALYTICAL VIEWS)
-- ============================================================================

-- 4.1 VIEW TỔNG QUAN DOANH THU & HÓA ĐƠN
CREATE OR ALTER VIEW dbo.vw_InvoiceRevenueReport
AS
SELECT 
    i.InvoiceID,
    i.InvoiceNumber,
    c.CustomerID,
    c.CustomerCode,
    c.FullName AS CustomerName,
    c.Email AS CustomerEmail,
    c.PhoneNumber AS CustomerPhone,
    i.SubtotalVND,
    i.DiscountVND,
    i.TaxVND,
    i.TotalAmountVND,
    i.PaymentMethod,
    i.PaymentStatus,
    i.TransactionReference,
    i.PaidAt,
    i.CreatedAt AS InvoiceDate,
    COUNT(d.DetailID) AS TotalItemCount
FROM dbo.Invoices i
INNER JOIN dbo.Customers c ON i.CustomerID = c.CustomerID
LEFT JOIN dbo.InvoiceDetails d ON i.InvoiceID = d.InvoiceID
GROUP BY 
    i.InvoiceID, i.InvoiceNumber, c.CustomerID, c.CustomerCode, c.FullName,
    c.Email, c.PhoneNumber, i.SubtotalVND, i.DiscountVND, i.TaxVND,
    i.TotalAmountVND, i.PaymentMethod, i.PaymentStatus, i.TransactionReference,
    i.PaidAt, i.CreatedAt;
GO

-- 4.2 VIEW TỔNG HỢP CÁC DỊCH VỤ ĐANG HOẠT ĐỘNG CỦA KHÁCH HÀNG
CREATE OR ALTER VIEW dbo.vw_CustomerActiveServices
AS
SELECT 
    cs.SubscriptionID,
    c.CustomerID,
    c.CustomerCode,
    c.FullName AS CustomerName,
    c.CustomerTier,
    c.CoinBalance,
    p.ProductID,
    p.ProductCode,
    cs.ServiceName,
    cat.CategoryName,
    cs.StartDate,
    cs.EndDate,
    cs.RemainingComicGenerations,
    cs.Status,
    CASE 
        WHEN cs.EndDate IS NULL THEN N'Vĩnh viễn'
        WHEN cs.EndDate >= GETDATE() THEN N'Còn hạn (' + CAST(DATEDIFF(day, GETDATE(), cs.EndDate) AS NVARCHAR(20)) + N' ngày)'
        ELSE N'Đã hết hạn'
    END AS ExpiryStatus
FROM dbo.CustomerServices cs
INNER JOIN dbo.Customers c ON cs.CustomerID = c.CustomerID
INNER JOIN dbo.Products p ON cs.ProductID = p.ProductID
INNER JOIN dbo.ProductCategories cat ON p.CategoryID = cat.CategoryID
WHERE cs.Status = N'ACTIVE';
GO

-- ============================================================================
-- 5. TẠO CÁC STORED PROCEDURES NGHIỆP VỤ (BUSINESS LOGIC)
-- ============================================================================

-- 5.1 STORED PROCEDURE: TẠO HÓA ĐƠN MỚI
CREATE OR ALTER PROCEDURE dbo.sp_CreateInvoice
    @CustomerID INT,
    @ProductID INT,
    @Quantity INT = 1,
    @PaymentMethod NVARCHAR(50) = N'VNPAY',
    @CustomerNotes NVARCHAR(500) = NULL,
    @NewInvoiceNumber NVARCHAR(50) OUTPUT,
    @NewInvoiceID INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        -- 1. Kiểm tra khách hàng và sản phẩm
        IF NOT EXISTS (SELECT 1 FROM dbo.Customers WHERE CustomerID = @CustomerID AND IsActive = 1)
        BEGIN
            RAISERROR(N'Khách hàng không tồn tại hoặc đã bị vô hiệu hóa.', 16, 1);
            RETURN;
        END

        DECLARE @PriceVND DECIMAL(18,2), @CoinsReward INT, @DurationDays INT, @MaxComic INT;
        SELECT 
            @PriceVND = PriceVND,
            @CoinsReward = CoinsReward,
            @DurationDays = DurationDays,
            @MaxComic = MaxComicGenerations
        FROM dbo.Products 
        WHERE ProductID = @ProductID AND IsActive = 1;

        IF @PriceVND IS NULL
        BEGIN
            RAISERROR(N'Sản phẩm không tồn tại hoặc không khả dụng.', 16, 1);
            RETURN;
        END

        -- 2. Sinh mã hóa đơn độc nhất
        DECLARE @TodayStr NVARCHAR(8) = CONVERT(NVARCHAR(8), GETDATE(), 112);
        DECLARE @Seq INT;
        SELECT @Seq = ISNULL(COUNT(*), 0) + 1 FROM dbo.Invoices WHERE InvoiceNumber LIKE 'INV-' + @TodayStr + '-%';
        SET @NewInvoiceNumber = 'INV-' + @TodayStr + '-' + RIGHT('0000' + CAST(@Seq AS NVARCHAR(10)), 4);

        DECLARE @Total DECIMAL(18,2) = @PriceVND * @Quantity;

        -- 3. Thêm hóa đơn
        INSERT INTO dbo.Invoices (
            InvoiceNumber, CustomerID, SubtotalVND, DiscountVND, TaxVND,
            TotalAmountVND, PaymentMethod, PaymentStatus, CustomerNotes
        )
        VALUES (
            @NewInvoiceNumber, @CustomerID, @Total, 0, 0,
            @Total, @PaymentMethod, N'PENDING', @CustomerNotes
        );

        SET @NewInvoiceID = SCOPE_IDENTITY();

        -- 4. Thêm chi tiết hóa đơn
        INSERT INTO dbo.InvoiceDetails (
            InvoiceID, ProductID, Quantity, UnitPriceVND, CoinsPerUnit, LineTotalVND
        )
        VALUES (
            @NewInvoiceID, @ProductID, @Quantity, @PriceVND, @CoinsReward, @Total
        );

        COMMIT TRANSACTION;
        PRINT N'==> Đã tạo hóa đơn thành công: ' + @NewInvoiceNumber;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrMsg, 16, 1);
    END CATCH
END;
GO

-- 5.2 STORED PROCEDURE: XÁC NHẬN THANH TOÁN THÀNH CÔNG & CỘNG XU / KÍCH HOẠT DỊCH VỤ
CREATE OR ALTER PROCEDURE dbo.sp_ProcessPaymentSuccess
    @InvoiceNumber NVARCHAR(50),
    @TransactionReference NVARCHAR(100),
    @AdminNotes NVARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @InvoiceID INT, @CustomerID INT, @PaymentStatus NVARCHAR(50), @TotalAmount DECIMAL(18,2);
        SELECT 
            @InvoiceID = InvoiceID,
            @CustomerID = CustomerID,
            @PaymentStatus = PaymentStatus,
            @TotalAmount = TotalAmountVND
        FROM dbo.Invoices
        WHERE InvoiceNumber = @InvoiceNumber;

        IF @InvoiceID IS NULL
        BEGIN
            RAISERROR(N'Không tìm thấy hóa đơn cần thanh toán.', 16, 1);
            RETURN;
        END

        IF @PaymentStatus = N'PAID'
        BEGIN
            PRINT N'Hóa đơn này đã được thanh toán trước đó.';
            COMMIT TRANSACTION;
            RETURN;
        END

        -- 1. Cập nhật trạng thái hóa đơn thành PAID
        UPDATE dbo.Invoices
        SET 
            PaymentStatus = N'PAID',
            TransactionReference = @TransactionReference,
            PaidAt = GETDATE(),
            AdminNotes = @AdminNotes,
            UpdatedAt = GETDATE()
        WHERE InvoiceID = @InvoiceID;

        -- 2. Duyệt từng sản phẩm trong hóa đơn để cộng Xu và Kích hoạt Dịch vụ
        DECLARE @ProductID INT, @Quantity INT, @CoinsReward INT, @DurationDays INT, @MaxComic INT, @ProductName NVARCHAR(150);
        
        DECLARE detail_cursor CURSOR FOR
        SELECT 
            d.ProductID, d.Quantity, p.CoinsReward, p.DurationDays, p.MaxComicGenerations, p.ProductName
        FROM dbo.InvoiceDetails d
        INNER JOIN dbo.Products p ON d.ProductID = p.ProductID
        WHERE d.InvoiceID = @InvoiceID;

        OPEN detail_cursor;
        FETCH NEXT FROM detail_cursor INTO @ProductID, @Quantity, @CoinsReward, @DurationDays, @MaxComic, @ProductName;

        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- 2A. Cộng xu nếu sản phẩm có thưởng xu
            IF @CoinsReward > 0
            BEGIN
                DECLARE @TotalCoins INT = @CoinsReward * @Quantity;
                DECLARE @OldBalance INT, @NewBalance INT;

                SELECT @OldBalance = CoinBalance FROM dbo.Customers WHERE CustomerID = @CustomerID;
                SET @NewBalance = @OldBalance + @TotalCoins;

                UPDATE dbo.Customers
                SET CoinBalance = @NewBalance, UpdatedAt = GETDATE()
                WHERE CustomerID = @CustomerID;

                -- Ghi nhật ký giao dịch xu
                INSERT INTO dbo.CoinTransactionLogs (
                    CustomerID, ActionType, AmountCoins, BalanceBefore, BalanceAfter,
                    ReferenceID, Description
                )
                VALUES (
                    @CustomerID, N'TOPUP', @TotalCoins, @OldBalance, @NewBalance,
                    @InvoiceNumber, N'Nạp xu từ hóa đơn ' + @InvoiceNumber + N' (' + @ProductName + N')'
                );
            END

            -- 2B. Kích hoạt dịch vụ / gói hội viên
            DECLARE @EndDate DATETIME2(3) = NULL;
            IF @DurationDays > 0
            BEGIN
                SET @EndDate = DATEADD(day, @DurationDays * @Quantity, GETDATE());
            END

            INSERT INTO dbo.CustomerServices (
                CustomerID, ProductID, InvoiceID, ServiceName, StartDate, EndDate,
                Status, RemainingComicGenerations
            )
            VALUES (
                @CustomerID, @ProductID, @InvoiceID, @ProductName, GETDATE(), @EndDate,
                N'ACTIVE', @MaxComic * @Quantity
            );

            FETCH NEXT FROM detail_cursor INTO @ProductID, @Quantity, @CoinsReward, @DurationDays, @MaxComic, @ProductName;
        END;

        CLOSE detail_cursor;
        DEALLOCATE detail_cursor;

        COMMIT TRANSACTION;
        PRINT N'==> Thanh toán thành công cho hóa đơn ' + @InvoiceNumber + N', đã cộng xu và kích hoạt gói dịch vụ!';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrMsg, 16, 1);
    END CATCH
END;
GO

-- 5.3 STORED PROCEDURE: TRỪ XU KHI KHÁCH HÀNG TẠO TRUYỆN TRANH / TRUYỆN CHỮ
CREATE OR ALTER PROCEDURE dbo.sp_DeductCustomerCoins
    @CustomerID INT,
    @Amount INT,
    @ActionType NVARCHAR(50),
    @ReferenceID NVARCHAR(100),
    @Description NVARCHAR(500),
    @Success BIT OUTPUT,
    @RemainingBalance INT OUTPUT,
    @Message NVARCHAR(255) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @CurrentBalance INT;
        SELECT @CurrentBalance = CoinBalance FROM dbo.Customers WHERE CustomerID = @CustomerID;

        IF @CurrentBalance IS NULL
        BEGIN
            SET @Success = 0;
            SET @Message = N'Không tìm thấy khách hàng.';
            ROLLBACK TRANSACTION;
            RETURN;
        END

        IF @CurrentBalance < @Amount
        BEGIN
            SET @Success = 0;
            SET @RemainingBalance = @CurrentBalance;
            SET @Message = N'Số dư xu không đủ (Hiện có: ' + CAST(@CurrentBalance AS NVARCHAR(20)) + N', Cần: ' + CAST(@Amount AS NVARCHAR(20)) + N').';
            ROLLBACK TRANSACTION;
            RETURN;
        END

        SET @RemainingBalance = @CurrentBalance - @Amount;

        UPDATE dbo.Customers
        SET CoinBalance = @RemainingBalance, UpdatedAt = GETDATE()
        WHERE CustomerID = @CustomerID;

        INSERT INTO dbo.CoinTransactionLogs (
            CustomerID, ActionType, AmountCoins, BalanceBefore, BalanceAfter,
            ReferenceID, Description
        )
        VALUES (
            @CustomerID, @ActionType, -@Amount, @CurrentBalance, @RemainingBalance,
            @ReferenceID, @Description
        );

        SET @Success = 1;
        SET @Message = N'Trừ xu thành công!';
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SET @Success = 0;
        SET @Message = ERROR_MESSAGE();
    END CATCH
END;
GO

-- ============================================================================
-- 6. CHÈN DỮ LIỆU MẪU BAN ĐẦU (SEED INITIAL SAMPLE DATA)
-- ============================================================================

-- 6.1 DANH MỤC
IF NOT EXISTS (SELECT 1 FROM dbo.ProductCategories WHERE CategoryCode = 'COIN_PACK')
BEGIN
    INSERT INTO dbo.ProductCategories (CategoryCode, CategoryName, Description, DisplayOrder)
    VALUES 
        (N'COIN_PACK', N'Gói Nạp Xu NarrAI', N'Các gói xu dùng để sáng tác truyện chữ và vẽ truyện tranh', 1),
        (N'VIP_SUBSCRIPTION', N'Gói Hội Viên Tác Giả VIP', N'Gói hội viên quyền lợi cao cấp và ưu tiên GPU ComfyUI', 2),
        (N'CUSTOM_SERVICE', N'Dịch Vụ Theo Yêu Cầu', N'Dịch vụ huấn luyện LoRA riêng và xuất bản độc quyền', 3);
END
GO

-- 6.2 SẢN PHẨM & BẢNG GIÁ DỊCH VỤ
IF NOT EXISTS (SELECT 1 FROM dbo.Products WHERE ProductCode = 'COIN_100')
BEGIN
    DECLARE @CatCoin INT = (SELECT CategoryID FROM dbo.ProductCategories WHERE CategoryCode = 'COIN_PACK');
    DECLARE @CatVIP INT = (SELECT CategoryID FROM dbo.ProductCategories WHERE CategoryCode = 'VIP_SUBSCRIPTION');
    DECLARE @CatCustom INT = (SELECT CategoryID FROM dbo.ProductCategories WHERE CategoryCode = 'CUSTOM_SERVICE');

    INSERT INTO dbo.Products (CategoryID, ProductCode, ProductName, Description, PriceVND, CoinsReward, DurationDays, MaxComicGenerations, IsHotPromo)
    VALUES 
        (@CatCoin, N'COIN_100', N'Túi Xu Khởi Đầu (100 Xu)', N'Đủ để tạo thêm 4 khung tranh Manga hoặc 5 chương truyện chữ', 20000, 100, 0, 4, 0),
        (@CatCoin, N'COIN_500', N'Rương Xu Tiết Kiệm (550 Xu)', N'Tặng thêm 50 xu khuyến mãi, tha hồ sáng tác', 100000, 550, 0, 20, 1),
        (@CatCoin, N'COIN_1200', N'Kho Báu Tác Giả (1400 Xu)', N'Tặng thêm 200 xu, mở khóa toàn bộ quyền năng sáng tác', 250000, 1400, 0, 50, 1),
        (@CatVIP, N'VIP_PRO_MONTH', N'Hội Viên VIP Manga Pro (30 Ngày)', N'Truy cập GPU ComfyUI siêu tốc, tặng 300 xu/tháng, 12 khung tranh miễn phí mỗi ngày', 199000, 300, 30, 100, 1),
        (@CatCustom, N'LORA_CUSTOM_TRAIN', N'Dịch Vụ Huấn Luyện LoRA Riêng', N'Tạo phong cách vẽ và tạo hình nhân vật độc quyền theo yêu cầu tác giả', 990000, 500, 0, 0, 0);
END
GO

-- 6.3 KHÁCH HÀNG MẪU
IF NOT EXISTS (SELECT 1 FROM dbo.Customers WHERE CustomerCode = 'CUST_001')
BEGIN
    INSERT INTO dbo.Customers (CustomerCode, Username, PasswordHash, FullName, Email, PhoneNumber, Address, City, CoinBalance, CustomerTier)
    VALUES 
        (N'CUST_001', N'dinhanh0701', N'pbkdf2_sha256$hashedpasswordexample123', N'Đinh Tuấn Anh', N'dinhanh070106@gmail.com', N'0988123456', N'12 Hoàng Diệu', N'Hà Nội', 500, N'VIP'),
        (N'CUST_002', N'author_vietnam', N'pbkdf2_sha256$hashedpasswordexample456', N'Nguyễn Văn Nam', N'namnguyen.author@gmail.com', N'0912345678', N'45 Nguyễn Huệ', N'Hồ Chí Minh', 150, N'Standard');
END
GO

-- 6.4 TẠO HÓA ĐƠN VÀ KÍCH HOẠT DỊCH VỤ MẪU
DECLARE @SampleCustID INT = (SELECT TOP 1 CustomerID FROM dbo.Customers WHERE CustomerCode = 'CUST_001');
DECLARE @SampleProdID INT = (SELECT TOP 1 ProductID FROM dbo.Products WHERE ProductCode = 'COIN_500');

IF @SampleCustID IS NOT NULL AND @SampleProdID IS NOT NULL AND NOT EXISTS (SELECT 1 FROM dbo.Invoices WHERE CustomerID = @SampleCustID)
BEGIN
    DECLARE @InvNum NVARCHAR(50), @InvID INT;
    EXEC dbo.sp_CreateInvoice 
        @CustomerID = @SampleCustID, 
        @ProductID = @SampleProdID, 
        @Quantity = 1, 
        @PaymentMethod = N'VNPAY', 
        @CustomerNotes = N'Nạp gói tiết kiệm 500 xu', 
        @NewInvoiceNumber = @InvNum OUTPUT, 
        @NewInvoiceID = @InvID OUTPUT;

    -- Xác nhận thanh toán thành công
    EXEC dbo.sp_ProcessPaymentSuccess 
        @InvoiceNumber = @InvNum, 
        @TransactionReference = N'VNPAY-TRANS-982173491', 
        @AdminNotes = N'Giao dịch tự động xác nhận qua webhook';
END
GO

PRINT N'============================================================================';
PRINT N'==> KHỞI TẠO CƠ SỞ DỮ LIỆU [NarrAI_CommerceDB] HOÀN TẤT THÀNH CÔNG!';
PRINT N'============================================================================';
GO
