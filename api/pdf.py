@api_view(['GET'])
def generate_driver_log_pdf(request):
    try:
        # Get the driver log data
        from datetime import datetime
        driver_log = LogSheet.objects.get(date=datetime.today())
        activities = driver_log.activities.all()
        
        # Get the absolute path to your PDF template
        template_path = os.path.join(settings.BASE_DIR, 'static', 'pdf_templates', 'blank-paper-log.pdf')
        
        # Check if file exists
        if not os.path.exists(template_path):
            return Response({'error': 'PDF template not found'}, status=404)
        
        # Create a buffer for the final PDF
        buffer = io.BytesIO()
        
        # Open the template PDF
        template_pdf = PdfReader(open(template_path, 'rb'))
        output_pdf = PdfWriter()
        
        # Add the template page to the output
        page = template_pdf.pages[0]
        output_pdf.add_page(page)
        
        # Create a canvas for overlaying data
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=letter)
        
        # Get driver info
        driver = DriverProfile.objects.get(user=request.user)
        
        # Set font before drawing text
        c.setFont("Helvetica", 10)
        
        # Draw text data on the canvas
        c.drawString(233.2, 731.0, driver_log.date.strftime('%m/%d/%Y'))
        c.drawString(117.6, 665.7, driver_log.trip.pickup_location)
        c.drawString(331.5, 667.7, driver_log.trip.dropoff_location)
        c.drawString(206.2, 604.3, str(driver_log.trip.distance))
        c.drawString(113.7, 548.6, driver.driver_license)
        
        # Define grid parameters 
        grid_start_x = 73.2
        grid_start_y = 412.4
        grid_width = 454.9
        grid_height = 19.2
        
        # Draw the grid framework
        c.setStrokeColorRGB(0, 0, 1)  # Blue for grid lines
        c.setLineWidth(1)
        
        # Draw horizontal grid lines
        for i in range(5):
            y = grid_start_y + (i * grid_height)
            c.line(grid_start_x, y, grid_start_x + grid_width, y)
        
        # Draw vertical grid lines (24 hours) and add time labels
        c.setFont("Helvetica", 6)  # Smaller font for time labels
        for i in range(25):
            # Calculate position for this vertical line
            x = grid_start_x + (i * (grid_width/24))
            
            # Draw the vertical line
            c.line(x, grid_start_y, x, grid_start_y + (4 * grid_height))
            
            # Calculate the hour for this line
            hour = i % 12
            if hour == 0:
                hour = 12  # Convert 0 to 12 for 12-hour format
            
            # Determine AM/PM
            am_pm = "AM" if i < 12 or i == 24 else "PM"
            
            # Special case for midnight and noon
            if i == 0:
                time_label = "MID"
            elif i == 12:
                time_label = "NOON"
            else:
                time_label = f"{hour}{am_pm}"
            
            # Position the label above the grid (10 units above the top line)
            label_y = grid_start_y + (4 * grid_height) + 10
            
            # Center the text on the line
            text_width = c.stringWidth(time_label, "Helvetica", 6)
            label_x = x - (text_width / 2)
            
            # Draw the time label
            c.drawString(label_x, label_y, time_label)
        
        # Label the grid rows
        c.setFont("Helvetica", 8)
        c.drawString(grid_start_x - 60, grid_start_y + (3 * grid_height), "OFF DUTY")
        c.drawString(grid_start_x - 60, grid_start_y + (2 * grid_height), "SLEEPER")
        c.drawString(grid_start_x - 60, grid_start_y + (1 * grid_height), "DRIVING")
        c.drawString(grid_start_x - 60, grid_start_y, "ON DUTY")
        
        # Define activity row positions (y-coordinates)
        activity_rows = {
            'OFF_DUTY': grid_start_y + (3 * grid_height),
            'SLEEPER': grid_start_y + (2 * grid_height),
            'Driving': grid_start_y + (1 * grid_height),
            'ON_DUTY': grid_start_y,
        }
        
        # Function to convert 12-hour time string to x-coordinate
        def time_to_x_coord(time_str):
            try:
                # Handle different possible 12-hour formats
                if ':' in time_str:
                    # Format like "2:30 PM" or "10:45 AM"
                    time_parts = time_str.strip().split(' ')
                    hour_minute = time_parts[0].split(':')
                    hour = int(hour_minute[0])
                    minute = int(hour_minute[1]) if len(hour_minute) > 1 else 0
                    am_pm = time_parts[1].upper() if len(time_parts) > 1 else 'AM'
                else:
                    # Format like "2 PM" or "10 AM"
                    time_parts = time_str.strip().split(' ')
                    hour = int(time_parts[0])
                    minute = 0
                    am_pm = time_parts[1].upper() if len(time_parts) > 1 else 'AM'
                
                # Convert to 24-hour format
                if am_pm == 'PM' and hour < 12:
                    hour += 12
                elif am_pm == 'AM' and hour == 12:
                    hour = 0
                
                # Calculate position on 24-hour grid
                hour_fraction = hour + (minute / 60)
                x_position = grid_start_x + (hour_fraction / 24) * grid_width
                return x_position
            except (ValueError, IndexError):
                # Return default position if conversion fails
                print(f"Could not parse time: {time_str}")
                return grid_start_x
        
        # Reset stroke color for activity lines
        c.setStrokeColorRGB(0, 0, 0)  # Black for activity lines
        
        # Draw activity lines
        for activity in activities:
            # Get y-coordinate for this activity type
            y_position = activity_rows.get(activity.activity_type, grid_start_y)
            
            # Get x-coordinates for start and end times
            start_x = time_to_x_coord(activity.start_time)
            end_x = time_to_x_coord(activity.end_time)
            
            # Set line properties
            c.setLineWidth(2)  # Line thickness
            
            # Draw the horizontal line
            c.line(start_x, y_position, end_x, y_position)
            
            # Draw small vertical markers at start and end
            c.line(start_x, y_position - 5, start_x, y_position + 5)
            c.line(end_x, y_position - 5, end_x, y_position + 5)
        
        # Finalize the canvas
        c.save()
        
        # Move to the beginning of the buffer
        packet.seek(0)
        
        # Create a PDF from the buffer
        overlay_pdf = PdfReader(packet)
        
        # Merge the overlay with the template page
        page.merge_page(overlay_pdf.pages[0])
        
        # Write the output PDF to the response buffer
        output_pdf.write(buffer)
        buffer.seek(0)
        
        # Create response with PDF
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="driver_log.pdf"'
        
        return response
        
    except LogSheet.DoesNotExist:
        return Response({'error': 'Log sheet not found'}, status=404)