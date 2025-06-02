# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models,tools
import csv
import os
import logging
from io import StringIO

_logger = logging.getLogger(__name__)

class StockLot(models.Model):
    _inherit = 'stock.lot'

    def create_lot_from_csv(self, file_path):
        """Create stock.lot records from CSV file based on S/N, skipping first 5 rows."""
        Product = self.env['product.product']
        Lot = self.env['stock.lot']

        # Check if file exists
        if not os.path.exists(file_path):
            _logger.error(f"CSV file not found at: {file_path}")
            return

        # Read CSV data
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                csv_content = f.read()
        except Exception as e:
            _logger.error(f"Error reading CSV file {file_path}: {str(e)}")
            return

        # Parse CSV data
        csv_file = StringIO(csv_content)
        reader = csv.reader(csv_file)

        # Skip first 5 rows
        for _ in range(5):
            try:
                next(reader, None)
            except StopIteration:
                _logger.error("CSV has fewer than 5 rows.")
                return

        # Assume headers for DictReader
        headers = ['S/N', 'Supplier name', 'Top', 'Base Color', 'HL', 'Length (inch)', 'Layer', 'Style', 'Size', 'EU', 'Status', 'Date Ordered', 'תאריך הגעה', 'Sold date', 'sales order customer name', 'Sale price', 'Product Title', 'Product Category']
        try:
            dict_reader = csv.DictReader(csv_file, fieldnames=headers)
            next(dict_reader, None)  # Skip the header row
        except StopIteration:
            _logger.error("CSV has no data rows after skipping 5 rows.")
            return

        for row in dict_reader:
            serial_number = row.get('S/N', '').strip()

            # Skip rows with missing S/N
            if not serial_number:
                _logger.warning("Skipping row with missing S/N.")
                continue

            # Search for existing product by S/N
            product = Product.search([
                ('default_code', '=', serial_number)
            ], limit=1)

            if not product:
                _logger.warning(f"No existing product found for S/N {serial_number}. Skipping.")
                continue

            # Check if stock.lot already exists with same name and product_id
            existing_lot = Lot.search([
                ('name', '=', serial_number),
                ('product_id', '=', product.id)
            ], limit=1)

            if existing_lot:
                _logger.info(f"Stock lot already exists: {existing_lot.name} (ID: {existing_lot.id}) for product: {product.name} (ID: {product.id}). Skipping.")
                continue

            # Create stock.lot
            try:
                lot = Lot.create({
                    'name': serial_number,
                    'product_id': product.id,
                })
                _logger.info(f"Created lot: {lot.name} (ID: {lot.id}) for product: {product.name} (ID: {product.id})")
            except Exception as e:
                _logger.error(f"Error creating stock lot for S/N {serial_number} and product {product.name}: {str(e)}")
                continue

        # Commit changes
        self.env.cr.commit()

    def cron_create_lot_from_csv(self):
        """Cron job to process CSV file."""
        file_path = tools.misc.file_path("bizzup_import_product/Product Data - Sheet.csv")
        if os.path.exists(file_path):
            _logger.info(f"Processing CSV file: {file_path}")
            self.create_lot_from_csv(file_path=file_path)
        else:
            _logger.error(f"CSV file not found at: {file_path}")