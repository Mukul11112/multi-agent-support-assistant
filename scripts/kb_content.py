"""
Source content for the TechMart Electronics knowledge base.

Each entry becomes one PDF in knowledge_base/. Content is deliberately
SPECIFIC (real SKUs, exact windows, exact fees) because vague policy text
makes RAG retrieval look broken during a demo.

Structure: {filename: {"title", "domain", "sections": [(heading, [paragraphs])]}}
The "domain" field is carried into vector-store metadata so each agent can
filter retrieval to its own documents.
"""

COMPANY = "TechMart Electronics"
SUPPORT_EMAIL = "support@techmart.example.com"
SUPPORT_PHONE = "1800-266-8278 (1800-CONTACT)"

KB = {
    "faq.pdf": {
        "title": "Frequently Asked Questions",
        "domain": "faq",
        "sections": [
            ("About TechMart Electronics", [
                "TechMart Electronics is an online consumer electronics retailer founded in 2016, "
                "headquartered in Pune, India, with fulfilment centres in Pune, Gurugram, and Bengaluru. "
                "We sell laptops, smartphones, audio equipment, smart home devices, and accessories.",
                "Registered office: TechMart Electronics Pvt. Ltd., 4th Floor, Aurora Tower, Baner Road, "
                "Pune 411045, Maharashtra, India. CIN: U52392PN2016PTC104772. GSTIN: 27AABCT9251H1ZQ.",
            ]),
            ("Contacting Support", [
                f"Email: {SUPPORT_EMAIL}. Phone: {SUPPORT_PHONE}. Live chat is available on techmart.example.com.",
                "Support hours are Monday to Saturday, 09:00 to 21:00 IST. We are closed on national holidays. "
                "Email tickets are answered within 24 business hours. Phone and chat queue times average under 4 minutes.",
                "Priority support (2-hour email response, 24x7 phone) is included with TechMart Premium membership.",
            ]),
            ("Accounts and Orders", [
                "You can create an account with an email address or an Indian mobile number. Guest checkout is "
                "supported but guest orders cannot be tracked in the order history page.",
                "Orders can be cancelled free of charge at any point before the order status changes to 'Shipped'. "
                "Once shipped, the order must be handled as a return under the Refund Policy.",
                "Order status values, in sequence, are: Placed, Payment Confirmed, Packed, Shipped, Out for Delivery, "
                "Delivered. A separate status, On Hold, indicates a payment or address verification issue.",
            ]),
            ("TechMart Premium", [
                "TechMart Premium costs INR 999 per year or INR 129 per month. It includes free next-day delivery on "
                "all orders, an extended 30-day return window (instead of 14 days), priority 24x7 support, and early "
                "access to sale events.",
                "Premium activates within 5 minutes of successful payment. If Premium has not activated 30 minutes "
                "after payment, this is a known provisioning issue - see the User Manual, section 'Premium not activating'.",
                "Premium can be cancelled any time. Annual plans cancelled within 14 days of purchase are refunded in "
                "full if no Premium delivery benefit has been used; after 14 days, refunds are pro-rated by unused months.",
            ]),
            ("Payments", [
                "We accept Visa, Mastercard, RuPay, American Express, UPI, net banking from 48 Indian banks, and "
                "TechMart Wallet. We do not accept cryptocurrency, cheques, or international cash transfers.",
                "Cash on Delivery (COD) is available for orders under INR 20,000 delivered to serviceable pincodes. "
                "A COD handling fee of INR 49 applies and is non-refundable once the order is shipped.",
                "No-cost EMI is available on orders above INR 8,000 with cards from HDFC, ICICI, Axis, SBI, and Kotak, "
                "for tenures of 3, 6, or 9 months.",
            ]),
            ("Privacy and Data", [
                "We store your name, contact details, addresses, and order history. We do not store full card numbers; "
                "payment credentials are tokenised by our PCI-DSS compliant payment processor.",
                "You may request deletion of your account and personal data by emailing " + SUPPORT_EMAIL +
                " with the subject line 'Data Deletion Request'. Deletion completes within 30 days, except for "
                "invoice records which we are legally required to retain for 8 years.",
            ]),
        ],
    },

    "refund_policy.pdf": {
        "title": "Refund and Returns Policy",
        "domain": "billing",
        "sections": [
            ("Return Window", [
                "Standard customers may return most items within 14 calendar days of delivery. TechMart Premium "
                "members have a 30 calendar day return window. The window is counted from the delivery timestamp "
                "recorded by the courier, not from the order date.",
                "Large appliances (air conditioners, refrigerators, washing machines) have a 7 calendar day return "
                "window because of reverse logistics constraints.",
            ]),
            ("Non-Returnable Items", [
                "The following cannot be returned once delivered: in-ear earphones and earbuds where the hygiene seal "
                "is broken; software licences and digital gift cards once the key is revealed; SIM cards; items marked "
                "'Final Sale' on the product page; and any item purchased more than 14 days ago (30 for Premium).",
                "Items damaged by the customer, missing serial numbers, or missing original accessories are not eligible "
                "for a full refund. A restocking deduction of up to 20% of the item value may be applied at TechMart's "
                "discretion when accessories or packaging are missing.",
            ]),
            ("How to Raise a Return", [
                "Go to Orders, select the order, click 'Return or Replace', choose a reason, and select a pickup slot. "
                "You will receive a Return Merchandise Authorisation (RMA) number by email immediately. Do not ship the "
                "item back without an RMA number; unauthorised shipments are refused at the warehouse.",
                "Reverse pickup is free for defective, damaged, or wrong items. For change-of-mind returns, a pickup fee "
                "of INR 99 is deducted from the refund. Premium members pay no pickup fee in any case.",
                "Pickup is attempted within 3 business days in metro pincodes and 5 business days elsewhere. Three failed "
                "pickup attempts close the RMA automatically; you must then raise a new return request if still within window.",
            ]),
            ("Refund Timelines", [
                "Refunds are initiated within 2 business days of the returned item passing quality check at our warehouse. "
                "Quality check itself takes 1 to 3 business days after the item reaches the warehouse.",
                "Once initiated, the money reaches you according to the original payment method: TechMart Wallet, instantly; "
                "UPI, 1 to 3 business days; debit card, 5 to 7 business days; credit card, 5 to 10 business days and it "
                "appears on your next statement; net banking, 3 to 5 business days; COD orders, refunded to a bank account "
                "you provide, in 5 to 7 business days.",
                "The total worst-case timeline from pickup to money-in-account is therefore about 15 business days for a "
                "credit card order. Refund reference numbers (ARN) are shared by email once the refund is initiated. If the "
                "money has not arrived 3 business days after the stated window, contact your bank with the ARN first.",
            ]),
            ("Replacements", [
                "Replacements are offered instead of refunds for defective items still under the return window, subject to "
                "stock. A replacement is dispatched only after the original item is picked up, except for TechMart Premium "
                "members, who receive an instant replacement dispatched before pickup.",
                "If a replacement is unavailable, the return is automatically converted to a refund and you are notified by email.",
            ]),
            ("Cancellations and Failed Payments", [
                "Orders cancelled before dispatch are refunded in full, including any COD fee, within 5 business days.",
                "If a payment is debited from your account but the order was not created, the amount is auto-reversed by the "
                "payment gateway within 5 to 7 business days without any action from you. If it has not reversed after 7 "
                "business days, contact support with the bank reference number.",
                "Duplicate charges for the same order are refunded within 3 business days of being reported.",
            ]),
            ("Escalation", [
                "If a refund is delayed beyond the stated timeline, you may escalate to the Refund Escalation Desk at "
                "refunds-escalation@techmart.example.com. Escalations are acknowledged within 4 business hours and resolved "
                "within 5 business days. Include your order ID and RMA number.",
                "Unresolved disputes may be raised with the TechMart Grievance Officer, Ms. R. Iyer, at "
                "grievance@techmart.example.com, as required under the Consumer Protection (E-Commerce) Rules, 2020. "
                "The Grievance Officer responds within 48 hours and resolves within 30 days.",
            ]),
        ],
    },

    "shipping_policy.pdf": {
        "title": "Shipping and Delivery Policy",
        "domain": "product",
        "sections": [
            ("Delivery Speeds and Charges", [
                "Standard delivery costs INR 49 and takes 3 to 6 business days. It is free on orders above INR 999. "
                "Express delivery costs INR 149 and takes 1 to 2 business days. Same-day delivery costs INR 249, is "
                "available in Pune, Mumbai, Bengaluru, and Gurugram only, and requires the order to be placed before 12:00 IST.",
                "TechMart Premium members receive free next-day delivery on every order with no minimum value.",
            ]),
            ("Serviceability", [
                "We deliver to 19,400 pincodes across India. Enter your pincode on the product page to check serviceability "
                "and the expected delivery date. We do not currently ship outside India.",
                "Large appliances are delivered only to pincodes with an installation partner. Delivery and installation are "
                "scheduled together and installation happens within 48 hours of delivery.",
            ]),
            ("Tracking", [
                "A tracking link and AWB (Airway Bill) number are emailed and sent by SMS when the order ships. Tracking data "
                "can take up to 12 hours after dispatch to appear on the courier's system - a link that shows 'no information' "
                "on the first day is normal and not a lost shipment.",
                "Our courier partners are Blue Dart for express, Delhivery for standard, and Porter for same-day.",
            ]),
            ("Delivery Attempts and Failures", [
                "Couriers make three delivery attempts on consecutive days. After three failed attempts, the shipment is "
                "returned to origin (RTO) and refunded automatically within 7 business days of reaching the warehouse.",
                "For orders above INR 25,000, an OTP sent to your registered mobile number is required at the doorstep. "
                "Delivery cannot be completed without it.",
                "If a package arrives visibly damaged or with a tampered seal, refuse the delivery. If you have already "
                "accepted it, report it within 48 hours with unboxing photographs, otherwise a damage claim cannot be filed "
                "with the courier.",
            ]),
            ("Delays", [
                "Delivery estimates exclude Sundays and national holidays. Delays commonly occur during festival sale periods "
                "(Diwali, Republic Day sale) and due to weather disruptions or local restrictions, which are outside our control.",
                "If a shipment shows no tracking movement for 5 consecutive business days, it is treated as a lost shipment. "
                "We will either dispatch a replacement or issue a full refund, at your choice, within 3 business days of the "
                "investigation being raised.",
            ]),
        ],
    },

    "warranty.pdf": {
        "title": "Warranty Policy",
        "domain": "technical",
        "sections": [
            ("Standard Warranty", [
                "All new products carry the manufacturer's warranty stated on the product page. Typical durations are: "
                "laptops 12 months, smartphones 12 months (6 months on in-box accessories such as chargers and cables), "
                "audio products 12 months, smart home devices 12 months, and large appliances 12 months on the unit with "
                "extended cover on specific components such as compressors (10 years) and motors (5 years).",
                "Warranty begins on the invoice date, not on the date of first use. Your TechMart tax invoice, downloadable "
                "from Orders, is a valid proof of purchase for all warranty claims.",
            ]),
            ("TechMart Care Extended Warranty", [
                "TechMart Care extends the manufacturer warranty by 12 or 24 additional months. It must be purchased within "
                "30 days of the product invoice date. Pricing is 6 to 9 percent of the product value depending on category.",
                "TechMart Care covers manufacturing defects and functional failures after the standard warranty expires. It "
                "does not convert into accidental or liquid damage cover, which is sold separately as TechMart Care+.",
            ]),
            ("What Is Not Covered", [
                "Physical damage, cracked screens, bent frames, liquid ingress, damage from voltage fluctuation without a "
                "surge protector, normal cosmetic wear, and consumable parts such as batteries degrading below 80 percent "
                "health through normal use are not covered.",
                "Warranty is void if the device has been opened or repaired by an unauthorised service centre, if the serial "
                "number or IMEI is removed or altered, or if the software has been modified in an unsupported way (rooting, "
                "jailbreaking, unlocking the bootloader).",
                "Software problems, data loss, and issues caused by third-party applications are not warranty items. Back up "
                "your data before any service visit; service centres are not liable for data on the device.",
            ]),
            ("Raising a Warranty Claim", [
                "For claims within 14 days of delivery (30 for Premium), raise a return through TechMart and we handle it as "
                "a defective return with a full refund or replacement.",
                "After the return window, warranty claims go directly to the manufacturer's authorised service centre. Find "
                "your nearest centre using the brand's service locator, carry the device with the TechMart tax invoice, and "
                "obtain a job sheet number. TechMart can help you locate the centre and follow up with the brand, but the "
                "repair decision rests with the manufacturer.",
                "Standard turnaround at service centres is 7 to 15 business days. If the brand declares the unit "
                "beyond economic repair, they issue a replacement or a credit note directly - TechMart does not refund "
                "post-window warranty failures.",
            ]),
        ],
    },

    "pricing.pdf": {
        "title": "Pricing, Offers, and Membership",
        "domain": "product",
        "sections": [
            ("Membership Plans", [
                "TechMart Basic is free and includes standard delivery charges, a 14-day return window, and support during "
                "business hours.",
                "TechMart Premium costs INR 999 per year or INR 129 per month. It includes free next-day delivery with no "
                "minimum order value, a 30-day return window, free reverse pickup, instant replacements, 24x7 priority "
                "support with a 2-hour email SLA, and early access to sale events 12 hours before Basic customers.",
                "TechMart Premium Business costs INR 4,999 per year, covers up to 5 users on one account, adds GST invoicing "
                "with company details, a dedicated account manager, and 30-day credit terms subject to approval.",
            ]),
            ("Current Product Pricing", [
                "Laptops: TechMart NoteBook Air 14 (SKU TM-NB-A14), INR 54,990. TechMart NoteBook Pro 16 (SKU TM-NB-P16), "
                "INR 1,04,990. TechMart NoteBook Go 13 (SKU TM-NB-G13), INR 32,990.",
                "Audio: TechMart Pulse Buds (SKU TM-AU-PB1), INR 3,499. TechMart Pulse Buds Pro (SKU TM-AU-PBP), INR 6,999. "
                "TechMart SoundBar 300 (SKU TM-AU-SB300), INR 12,499.",
                "Smart home: TechMart SmartPlug Mini (SKU TM-SH-SP1), INR 899. TechMart SmartCam 360 (SKU TM-SH-C360), "
                "INR 3,299. TechMart SmartBulb RGB (SKU TM-SH-BR1), INR 649.",
                "Accessories: TechMart 65W GaN Charger (SKU TM-AC-C65), INR 2,199. TechMart Laptop Sleeve 14 (SKU TM-AC-S14), "
                "INR 999. TechMart Wireless Mouse (SKU TM-AC-WM1), INR 749.",
            ]),
            ("Product Comparison: NoteBook Range", [
                "NoteBook Go 13: 13.3-inch 1920x1080 display, Intel Core i3-1215U, 8 GB LPDDR5, 256 GB SSD, 1.24 kg, "
                "9-hour battery, 2 USB-C and 1 USB-A port. Best for students and light office use.",
                "NoteBook Air 14: 14-inch 2240x1400 display, Intel Core i5-1340P, 16 GB LPDDR5, 512 GB SSD, 1.31 kg, "
                "13-hour battery, 2 Thunderbolt 4 and 1 USB-A port, backlit keyboard. Best all-rounder for professionals.",
                "NoteBook Pro 16: 16-inch 3072x1920 120 Hz display, Intel Core i7-13700H with RTX 4050, 32 GB DDR5, 1 TB SSD, "
                "1.95 kg, 8-hour battery, 2 Thunderbolt 4, HDMI 2.1, SD card reader. Best for video editing, CAD, and "
                "development workloads.",
                "In short: choose Go 13 for budget and portability, Air 14 for the best balance of weight and battery, and "
                "Pro 16 for raw performance where battery life and weight matter less.",
            ]),
            ("Offers and Price Guarantees", [
                "Coupon codes apply to the cart subtotal before delivery charges and cannot be combined - only one coupon per "
                "order. Bank offers stack with coupons and are applied at the payment step.",
                "We do not price-match other retailers. We do offer a 7-day price drop protection on TechMart's own price: if "
                "the price of an item you bought drops on techmart.example.com within 7 days of your invoice date, contact "
                "support for the difference as TechMart Wallet credit. Price drop protection excludes sale events such as "
                "Big Billion Days and Diwali Dhamaka.",
                "Prices include GST. GST rate on most electronics is 18 percent. Business customers can download a GST invoice "
                "from Orders after adding their GSTIN to the account before placing the order - GSTINs cannot be added after "
                "an order is invoiced.",
            ]),
        ],
    },

    "products.pdf": {
        "title": "Product Catalogue and Specifications",
        "domain": "product",
        "sections": [
            ("Catalogue Overview", [
                "TechMart Electronics stocks four in-house categories - NoteBook laptops, Pulse audio, SmartHome devices, "
                "and accessories - alongside third-party brands. This document covers in-house products only; third-party "
                "specifications are on the individual product pages.",
            ]),
            ("NoteBook Laptops", [
                "NoteBook Go 13 (TM-NB-G13, INR 32,990): 13.3-inch FHD IPS 250 nits, Core i3-1215U, Intel UHD graphics, "
                "8 GB LPDDR5 soldered, 256 GB PCIe Gen3 SSD, 45 Wh battery, 45 W charger, Wi-Fi 6, no fingerprint reader, "
                "1.24 kg. Colours: Graphite, Silver. RAM is not upgradeable; the SSD is replaceable with an M.2 2242 drive.",
                "NoteBook Air 14 (TM-NB-A14, INR 54,990): 14-inch 2.2K IPS 400 nits, Core i5-1340P, Iris Xe graphics, "
                "16 GB LPDDR5 soldered, 512 GB PCIe Gen4 SSD, 60 Wh battery, 65 W GaN charger, Wi-Fi 6E, fingerprint reader "
                "in power button, backlit keyboard, 1080p webcam, 1.31 kg. Colours: Graphite, Silver, Midnight Blue.",
                "NoteBook Pro 16 (TM-NB-P16, INR 1,04,990): 16-inch 3K 120 Hz mini-LED 600 nits, Core i7-13700H, NVIDIA "
                "RTX 4050 6 GB, 32 GB DDR5 in two SO-DIMM slots (upgradeable to 64 GB), 1 TB PCIe Gen4 SSD with a second "
                "free M.2 slot, 90 Wh battery, 140 W charger, Wi-Fi 6E, per-key backlighting, 1.95 kg. Colour: Graphite.",
            ]),
            ("Pulse Audio", [
                "Pulse Buds (TM-AU-PB1, INR 3,499): 10 mm drivers, Bluetooth 5.3, 6 hours per charge and 24 hours with the "
                "case, USB-C charging, IPX4 splash resistance, no active noise cancellation, 40 ms low-latency game mode.",
                "Pulse Buds Pro (TM-AU-PBP, INR 6,999): 11 mm drivers, Bluetooth 5.3 with LE Audio, hybrid ANC up to 45 dB, "
                "transparency mode, 8 hours per charge and 32 hours with the case, wireless charging case, IPX5, multipoint "
                "pairing to two devices, in-app EQ.",
                "SoundBar 300 (TM-AU-SB300, INR 12,499): 2.1 channel, 300 W peak, wireless subwoofer, HDMI eARC, optical, "
                "Bluetooth 5.2, Dolby Audio, wall-mountable, remote included.",
            ]),
            ("SmartHome", [
                "SmartPlug Mini (TM-SH-SP1, INR 899): 16 A, 2.4 GHz Wi-Fi only, energy monitoring, scheduling, works with "
                "Alexa and Google Home, no hub required.",
                "SmartCam 360 (TM-SH-C360, INR 3,299): 2K resolution, 360 degree pan and 110 degree tilt, night vision to "
                "10 m, two-way audio, motion and person detection, microSD up to 256 GB, optional cloud plan at INR 199 per "
                "month, 2.4 GHz Wi-Fi only.",
                "SmartBulb RGB (TM-SH-BR1, INR 649): 9 W, B22 base, 16 million colours, tunable white 2700K to 6500K, "
                "2.4 GHz Wi-Fi, group control, sunrise and sunset schedules.",
                "Note: all SmartHome devices are 2.4 GHz only. They will not connect on a 5 GHz network. On dual-band "
                "routers that use one combined SSID, temporarily separate the bands or disable 5 GHz during setup.",
            ]),
            ("Stock and Availability", [
                "In Stock means dispatch within 24 hours. Limited Stock means fewer than 10 units remain at your nearest "
                "fulfilment centre. Pre-order means the product ships on the date stated on the product page and is charged "
                "at the time of ordering. Out of Stock items show a 'Notify Me' button; notifications are sent by email and "
                "do not reserve stock.",
                "Restock timelines are estimates and are not guaranteed. We do not accept backorders on Out of Stock items.",
            ]),
        ],
    },

    "installation_guide.pdf": {
        "title": "Installation and Setup Guide",
        "domain": "technical",
        "sections": [
            ("TechMart Account Setup", [
                "Download the TechMart app from the Play Store or App Store, or use techmart.example.com. Register with an "
                "email address or mobile number. A 6-digit OTP is sent for verification and is valid for 10 minutes. "
                "OTP SMS can be delayed on some networks - wait 60 seconds before requesting a resend, and note that "
                "requesting a resend invalidates the previous OTP.",
                "If you do not receive an OTP after two attempts, switch to email verification from the same screen, or use "
                "'Sign in with Google'.",
            ]),
            ("NoteBook First-Time Setup", [
                "Charge for 30 minutes before first power-on. Press and hold the power button for 2 seconds. Follow the "
                "Windows out-of-box setup: select region, connect Wi-Fi, sign in with a Microsoft account, and set up "
                "fingerprint or PIN.",
                "Run TechMart Update Assistant, pre-installed on the desktop, before anything else. It installs the current "
                "chipset, graphics, and firmware drivers. Setup requires an internet connection and takes 10 to 20 minutes.",
                "The first boot may take up to 5 minutes and the fan may run loudly while Windows indexes files. This is "
                "expected and settles within the first hour of use.",
            ]),
            ("Pulse Buds Pairing", [
                "Open the case near the device. The buds enter pairing mode automatically on first use, indicated by a "
                "flashing white LED. Select 'TechMart Pulse Buds' from the Bluetooth menu.",
                "To pair to a new device later, place both buds in the case, keep the lid open, and hold the case button for "
                "5 seconds until the LED flashes white again.",
                "To factory reset, place both buds in the case, keep the lid open, and hold the case button for 15 seconds "
                "until the LED flashes red three times. Then remove the old pairing entry from your phone's Bluetooth "
                "settings before re-pairing, otherwise the stale bond will block reconnection.",
            ]),
            ("SmartHome Device Setup", [
                "Install the TechMart Home app. Connect your phone to the 2.4 GHz Wi-Fi network you want the device to use - "
                "the app copies the credentials from the phone's current network, so joining a 5 GHz network at this step is "
                "the most common cause of setup failure.",
                "Power the device on. Press and hold its reset button for 5 seconds until the LED blinks rapidly, which "
                "indicates pairing mode. In the app, tap Add Device, select the product, and enter the Wi-Fi password.",
                "Setup fails most often because of: a 5 GHz network, a password containing special characters the device "
                "firmware rejects, MAC address filtering enabled on the router, AP isolation or client isolation enabled, or "
                "the device being more than 10 m from the router during setup.",
            ]),
            ("SoundBar 300 Installation", [
                "Connect the SoundBar to the TV's HDMI eARC or ARC port with the supplied HDMI cable. Enable HDMI-CEC on the "
                "TV (named Anynet+ on Samsung, Bravia Sync on Sony, SIMPLINK on LG) and set the TV audio output to 'External "
                "speaker' or 'Receiver'.",
                "The subwoofer pairs automatically within 30 seconds of both units being powered on. If the subwoofer LED "
                "keeps blinking, hold the PAIR button on its rear for 5 seconds with the SoundBar already on.",
                "For wall mounting, use the supplied bracket and keep at least 5 cm of clearance below the TV. Do not enclose "
                "the SoundBar in a cabinet - it blocks the bass ports.",
            ]),
        ],
    },

    "user_manual.pdf": {
        "title": "User Manual and Troubleshooting",
        "domain": "technical",
        "sections": [
            ("Login and Password", [
                "To reset your password, go to the login page, click 'Forgot Password', enter your registered email, and "
                "follow the link sent to you. The reset link is valid for 30 minutes and can be used only once. Check your "
                "spam folder if the email has not arrived within 5 minutes.",
                "Accounts lock for 30 minutes after 5 consecutive failed login attempts. The lock clears automatically; "
                "support cannot unlock it early. Resetting your password clears the lock immediately.",
                "If you registered with 'Sign in with Google', your account has no TechMart password. Use the Google button "
                "rather than 'Forgot Password'. To add a password, sign in with Google, then go to Account, Security, "
                "Set Password.",
                "Being logged out repeatedly is usually caused by browser settings that block cookies, an aggressive privacy "
                "extension, or the system clock being wrong by more than 5 minutes, which invalidates the session token.",
            ]),
            ("Premium Not Activating After Payment", [
                "Premium normally activates within 5 minutes of payment. If it has not activated after 30 minutes but your "
                "bank shows the amount debited, the cause is almost always a payment webhook that did not reach our servers, "
                "so the payment succeeded but the entitlement was never provisioned.",
                "First, fully sign out and sign back in - the entitlement is cached in your session token and a stale token "
                "shows Premium as locked even after provisioning succeeds. Force-close the app rather than just backgrounding "
                "it. On the web, hard refresh with Ctrl+Shift+R.",
                "If it is still locked, contact support with the payment reference number from your bank statement. Support "
                "can reconcile the payment and provision Premium manually, usually within 2 hours. Do not pay a second time - "
                "duplicate payments are refunded but take 3 business days to reverse.",
                "This is a joint billing and technical issue: the payment side is confirmed by the reference number, and the "
                "entitlement side is fixed by re-provisioning and clearing the session.",
            ]),
            ("NoteBook Troubleshooting", [
                "Device will not power on: hold the power button for 15 seconds to force a hard reset, connect the original "
                "charger, and wait 15 minutes. A charging LED that does not light indicates a charger or port fault - test "
                "with a second USB-C PD charger of at least 65 W before booking a service visit.",
                "Battery draining fast: check Windows Settings, System, Power and Battery, Battery Usage for apps consuming "
                "power in the background. Battery health below 80 percent after 800 charge cycles is normal wear and is not "
                "covered under warranty.",
                "Overheating or loud fans: ensure the vents are not blocked, run TechMart Update Assistant to install the "
                "current thermal firmware, and check Task Manager for a process pinned at high CPU. Sustained fan noise on a "
                "new machine during Windows indexing is expected for the first hour.",
                "Wi-Fi keeps disconnecting: update the Wi-Fi driver through TechMart Update Assistant, disable 'Allow the "
                "computer to turn off this device to save power' in the adapter's Device Manager properties, and switch the "
                "router band to 5 GHz where available.",
                "Blue screen errors: note the STOP code shown on screen. Run Windows Update, run TechMart Update Assistant, "
                "and run 'sfc /scannow' from an elevated command prompt. Recurring blue screens with the same STOP code after "
                "these steps indicate a hardware fault and need a service centre job sheet.",
            ]),
            ("Pulse Buds Troubleshooting", [
                "Only one bud plays audio: place both buds in the case, close the lid for 10 seconds, and reopen. If the "
                "problem persists, factory reset the buds (hold the case button for 15 seconds with the lid open) and remove "
                "the stale pairing entry from the phone before re-pairing.",
                "Buds will not charge: clean the metal contacts on the buds and inside the case with a dry cotton swab. "
                "Contact fouling from ear wax is the most common cause. Ensure the case itself has charge - the case LED "
                "shows red when below 20 percent.",
                "Audio cutting out: Bluetooth interference from 2.4 GHz Wi-Fi and USB 3.0 devices is common. Move away from "
                "the router, disable multipoint if you are not using two devices, and confirm no third device is trying to "
                "auto-reconnect.",
                "Microphone not working on calls: check the app permissions for Bluetooth on Android 12 and above, where a "
                "missing 'Nearby devices' permission silently disables the headset profile.",
            ]),
            ("SmartHome Troubleshooting", [
                "Device offline in the app: confirm the router is on 2.4 GHz, check that fewer than 32 clients are connected "
                "to the 2.4 GHz band, and power-cycle the device. If it stays offline, reset it (5 second button hold) and "
                "re-add it in the app.",
                "SmartCam feed lagging: 2K streaming needs at least 4 Mbps upload. Reduce the stream to HD in the app if your "
                "upload speed is lower. A microSD card that is not marked Class 10 or above will cause recording gaps.",
                "SmartBulb loses its schedule after a power cut: schedules are stored in the cloud and re-sync when the bulb "
                "reconnects, which can take up to 10 minutes. If the bulb was reset by five rapid power cycles, it has "
                "returned to factory state and must be re-added.",
            ]),
            ("When to Contact Support", [
                "Contact support if: the device is dead on arrival, a fault persists after the steps above, you need an RMA "
                "for a return, your refund is past the stated timeline, or you need help locating an authorised service "
                "centre. Have your order ID, the device serial number, and a description of what you have already tried.",
            ]),
        ],
    },
}
