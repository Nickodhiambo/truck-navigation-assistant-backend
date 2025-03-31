@api_view(['GET'])
def generate_driver_log_pdf(request, log_sheet_id):
    try:
        # Get the log sheet and its activities
        log_sheet = LogSheet.objects.get(id=log_sheet_id)
        activities = log_sheet.activities.all()
        
        # Create a buffer for the PDF
        buffer = io.BytesIO()
        
        # Get template path
        template_path = os.path.join(settings.BASE_DIR, 'static', 'pdf_templates', 'driver_log_template.pdf')
        
        if not os.path.exists(template_path):
            return Response({'error': 'PDF template not found'}, status=404)
        
        # Open the template PDF
        template_pdf = PdfReader(open(template_path, 'rb'))
        output_pdf = PdfWriter()
        
        # Get the first page of the template
        template_page = template_pdf.pages[0]
        output_pdf.add_page(template_page)
        
        # Create overlay for data
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=letter)
        
        # Define grid parameters (adjust these to match your template)
        grid_start_x = 100  # Left edge of grid
        grid_start_y = 400  # Bottom edge of grid
        grid_width = 500    # Total width of the 24-hour grid
        grid_height = 160   # Total height of the activity grid
        
        # Define activity row positions (y-coordinates)
        activity_rows = {
            'OFF_DUTY': grid_start_y + grid_height * 0.8,
            'SLEEPER': grid_start_y + grid_height * 0.6,
            'Driving': grid_start_y + grid_height * 0.4,
            'ON_DUTY': grid_start_y + grid_height * 0.2,
        }
        
        # Function to convert time string to x-coordinate
        def time_to_x_coord(time_str):
            # Assuming time_str is in 24-hour format like "14:30"
            try:
                if ':' in time_str:
                    hour, minute = map(int, time_str.split(':'))
                else:
                    # If it's just an hour value (e.g., "14")
                    hour = int(time_str)
                    minute = 0
                
                # Calculate position (24-hour grid)
                hour_fraction = hour + (minute / 60)
                x_position = grid_start_x + (hour_fraction / 24) * grid_width
                return x_position
            except ValueError:
                # Return default position if conversion fails
                return grid_start_x
        
        # Draw activity lines
        for activity in activities:
            # Get y-coordinate for this activity type
            y_position = activity_rows.get(activity.activity_type, grid_start_y)
            
            # Get x-coordinates for start and end times
            start_x = time_to_x_coord(activity.start_time)
            end_x = time_to_x_coord(activity.end_time)
            
            # Set line properties
            c.setStrokeColorRGB(0, 0, 0)  # Black line
            c.setLineWidth(2)             # Line thickness
            
            # Draw the horizontal line
            c.line(start_x, y_position, end_x, y_position)
            
            # Draw small vertical markers at start and end (optional)
            c.line(start_x, y_position - 5, start_x, y_position + 5)
            c.line(end_x, y_position - 5, end_x, y_position + 5)
            
            # Add activity description if space permits
            if end_x - start_x > 50:  # Only add text if there's enough space
                c.setFont("Helvetica", 8)
                text_width = c.stringWidth(activity.description, "Helvetica", 8)
                if text_width < (end_x - start_x):
                    c.drawString(start_x + 5, y_position + 8, activity.description)
            
            # Add location text below the grid (optional)
            if activity.location:
                c.setFont("Helvetica", 8)
                c.drawString(start_x, grid_start_y - 15, activity.location)
        
        # Add other driver log information as needed
        # (Fill in other data fields from log_sheet)
        
        c.save()
        
        # Merge the template with the overlay
        overlay_buffer.seek(0)
        overlay_pdf = PdfReader(overlay_buffer)
        template_page.merge_page(overlay_pdf.pages[0])
        
        # Write the output PDF to the response buffer
        output_pdf.write(buffer)
        buffer.seek(0)
        
        # Create response with PDF
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="driver_log_{log_sheet_id}.pdf"'
        
        return response
        
    except LogSheet.DoesNotExist:
        return Response({'error': 'Log sheet not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)