import pandas as pd
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

def export_to_excel(invoices):
    """
    Export invoices to Excel file using pandas and openpyxl
    Returns BytesIO object for file download
    """
    try:
        # Prepare data for DataFrame
        data = []
        
        for invoice in invoices:
            # Basic invoice info
            base_data = {
                'Invoice ID': invoice.id,
                'Invoice Number': invoice.invoice_number or 'N/A',
                'Date': invoice.invoice_date or 'N/A',
                'Vendor Name': invoice.vendor_name or 'N/A',
                'Vendor Address': invoice.vendor_address or 'N/A',
                'Customer Name': invoice.customer_name or 'N/A',
                'Customer Address': invoice.customer_address or 'N/A',
                'Subtotal': invoice.subtotal or 'N/A',
                'Tax Amount': invoice.tax_amount or 'N/A',
                'Total Amount': invoice.total_amount or 'N/A',
                'Uploaded By': invoice.user.username,
                'Upload Date': invoice.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add items
            items = invoice.get_items()
            if items:
                for idx, item in enumerate(items, 1):
                    item_data = base_data.copy()
                    item_data['Item #'] = idx
                    item_data['Item Description'] = item.get('description', 'N/A')
                    item_data['Quantity'] = item.get('quantity', 'N/A')
                    item_data['Unit Price'] = item.get('unit_price', 'N/A')
                    item_data['Item Total'] = item.get('total', 'N/A')
                    data.append(item_data)
            else:
                data.append(base_data)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Invoices')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Invoices']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        logger.info(f"Successfully exported {len(invoices)} invoices to Excel")
        return output
    
    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}")
        raise Exception(f"Failed to export to Excel: {str(e)}")
