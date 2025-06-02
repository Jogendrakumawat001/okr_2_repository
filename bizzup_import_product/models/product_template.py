# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

import csv
import logging
import os
import re
import time
import uuid
from datetime import datetime, timedelta

from odoo import models, fields, api, tools
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'Product Template with CSV Import'

    by_pass_variant_creation = fields.Boolean()



    def _create_variant_ids(self):
        if not self.by_pass_variant_creation:
            return super()._create_variant_ids()

    def clean_value(self, value):
        """Clean input value by trimming and handling empty or invalid values."""
        if (value is None or value == '' or value == '#N/A' or value ==
            '#ref!') or value == 'None':
            return False
        if isinstance(value, str):
            cleaned = value.strip().replace('"', '')
            return cleaned if cleaned else False
        return value

    def parse_sale_price(self, price_str):
        """Parse sale price by removing currency symbols and converting to float."""
        if not price_str or price_str == '':
            return 0.0
        try:
            cleaned_price = re.sub(r'[^\d,.]', '', price_str).replace(',', '')
            return float(cleaned_price)
        except (ValueError, TypeError):
            _logger.warning(f"Invalid sale price format: {price_str}")
            return 0.0

    def parse_date(self, date_str):
        """Parse date string or Excel serial date to Odoo date format, supporting multiple formats."""
        if not date_str or date_str == '':
            return False
        try:
            # Handle Excel serial date numbers (e.g., 44180)
            if isinstance(date_str, (int, float)) or str(date_str).isdigit():
                excel_epoch = datetime(1899, 12, 30)
                parsed_date = excel_epoch + timedelta(days=float(date_str))
                return parsed_date.date()
            # Try multiple date formats
            date_formats = ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d']
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str,
                                                    date_format).date()
                    return parsed_date
                except ValueError:
                    continue
            _logger.warning(f"Invalid date format: {date_str}")
            return False
        except (ValueError, TypeError):
            _logger.warning(f"Invalid date format: {date_str}")
            return False

    def get_or_create_category(self, category_name, category_cache):
        """Get or create a product category, using cache to avoid repeated queries."""
        if not category_name:
            category_name = 'Miscellaneous'  # Default category
            _logger.debug(
                f"No category provided, using default: {category_name}")
        if category_name in category_cache:
            _logger.debug(
                f"Category cache hit: {category_name} (ID: {category_cache[category_name]})")
            return category_cache[category_name]
        category = self.env['product.category'].search(
            [('name', '=', category_name)], limit=1)
        if not category:
            category = self.env['product.category'].create({
                'name': category_name,
                'parent_id': False,
            })
            _logger.debug(
                f"Created new category: {category_name} (ID: {category.id})")
        category_cache[category_name] = category.id
        return category.id

    def get_or_create_supplier(self, supplier_name, supplier_cache):
        """Get or create a supplier (res.partner), using cache to avoid repeated queries."""
        if not supplier_name:
            return False
        if supplier_name in supplier_cache:
            _logger.debug(
                f"Supplier cache hit: {supplier_name} (ID: {supplier_cache[supplier_name]})")
            return supplier_cache[supplier_name]
        supplier = self.env['res.partner'].search(
            ['|', ('name', '=', supplier_name),
             ('name', '=', supplier_name.lower()),
             ('supplier_rank', '>', 0)],
            limit=1)
        if not supplier:
            supplier = self.env['res.partner'].create({
                'name': supplier_name,
                'supplier_rank': 1,
            })
            _logger.debug(
                f"Created new supplier: {supplier_name} (ID: {supplier.id})")
        supplier_cache[supplier_name] = supplier.id
        return supplier.id

    def get_or_create_attribute(self, attribute_name, value, attribute_cache,
                                value_cache):
        """Get or create a product attribute and its value, using caches, without creating variants."""
        if not value or not attribute_name:
            return False, False
        # Check attribute cache
        if attribute_name in attribute_cache:
            attr_id = attribute_cache[attribute_name]
            _logger.debug(
                f"Attribute cache hit: {attribute_name} (ID: {attr_id})")
        else:
            attribute = self.env['product.attribute'].search(
                ['|', ('name', '=', attribute_name),
                 ('name', '=', attribute_name.lower())], limit=1)
            if not attribute:
                attribute = self.env['product.attribute'].create({
                    'name': attribute_name,
                    'create_variant': 'no_variant',
                    # Prevent variant creation
                })
                _logger.debug(
                    f"Created new attribute: {attribute_name} (ID: {attribute.id})")
            attribute_cache[attribute_name] = attribute.id
            attr_id = attribute.id

        # Check value cache
        cache_key = (attr_id, value)
        if cache_key in value_cache:
            _logger.debug(
                f"Attribute value cache hit: {value} for {attribute_name} (ID: {value_cache[cache_key]})")
            return attr_id, value_cache[cache_key]
        value_obj = self.env['product.attribute.value'].search([
            ('attribute_id', '=', attr_id),
            ('name', '=', value)
        ], limit=1)
        if not value_obj:
            value_obj = self.env['product.attribute.value'].create({
                'attribute_id': attr_id,
                'name': value,
            })
            _logger.debug(
                f"Created new attribute value: {value} for {attribute_name} (ID: {value_obj.id})")
        value_cache[cache_key] = value_obj.id
        return attr_id, value_obj.id

    def update_product_template_attributes(self, product_template, attributes,
                                           attribute_cache, value_cache):
        """Update product template attributes, preventing duplicates."""
        _logger.debug(
            f"Updating attributes for product: {product_template.name} (ID: {product_template.id})")
        existing_lines = product_template.attribute_line_ids
        existing_attribute_ids = set(existing_lines.mapped('attribute_id.id'))
        existing_value_map = {line.attribute_id.id: set(line.value_ids.ids)
                              for line in existing_lines}

        for attr_name, attr_value in attributes.items():
            attr_id, value_id = self.get_or_create_attribute(attr_name,
                                                             attr_value,
                                                             attribute_cache,
                                                             value_cache)
            if not attr_id or not value_id:
                _logger.debug(
                    f"Skipping invalid attribute {attr_name} with value {attr_value} for {product_template.name}")
                continue

            # Check for existing attribute line
            if attr_id in existing_attribute_ids:
                line = existing_lines.filtered(
                    lambda l: l.attribute_id.id == attr_id)
                if value_id in line.value_ids.ids:
                    _logger.debug(
                        f"Skipping duplicate attribute {attr_name} with value {attr_value} for {product_template.name} (Attribute ID: {attr_id}, Value ID: {value_id})")
                    continue
                # Update existing line with new value
                line.value_ids = [(4, value_id)]
                _logger.debug(
                    f"Updated attribute {attr_name} with value {attr_value} for {product_template.name} (Attribute ID: {attr_id}, Value ID: {value_id})")
            else:
                # Create new attribute line
                self.env['product.template.attribute.line'].create({
                    'product_tmpl_id': product_template.id,
                    'attribute_id': attr_id,
                    'value_ids': [(6, 0, [value_id])],
                })
                _logger.debug(
                    f"Added attribute {attr_name} with value {attr_value} to {product_template.name} (Attribute ID: {attr_id}, Value ID: {value_id})")

    def parse_product_name(self, product_title):
        """Extract product name by removing S/N (e.g., 'Regular Fall (#10001)' → 'Regular Fall')."""
        if not product_title:
            return False
        cleaned_name = re.sub(r'\s*\(#\d+\)', '', product_title).strip()
        return cleaned_name if cleaned_name else False

    def process_product_template(self, data, category_cache, attribute_cache,
                                 value_cache, row_number, total_rows):
        """Process a single row of CSV data to create or update a product template."""
        start_time = time.time()
        product_title = self.parse_product_name(
            self.clean_value(data.get('Product Title')))
        default_code = self.clean_value(
            data.get('S/N')) or f"PROD-{uuid.uuid4().hex[:8]}"

        if not product_title:
            product_title = 'Empty Product'

        _logger.debug(
            f"Row {row_number}/{total_rows}: Processing product: {product_title} (S/N: {default_code})")

        # Extract fields
        supplier_name = self.clean_value(data.get('Supplier name'))
        status = self.clean_value(data.get('Status'))
        sale_price = self.parse_sale_price(data.get('Sale price')) or 0.0
        category_name = self.clean_value(data.get('Product Category'))
        eu_field = self.clean_value(data.get('EU'))

        # Extract attributes
        attributes = {
            'Top': self.clean_value(data.get('Top')),
            'Base Color': self.clean_value(data.get('Base Color')),
            'HL': self.clean_value(data.get('HL')),
            'Length': self.clean_value(data.get('Length (inch)')),
            'Layer': self.clean_value(data.get('Layer')),
            'Style': self.clean_value(data.get('Style')),
            'Size': self.clean_value(data.get('Size')),
        }
        attributes = {k: v for k, v in attributes.items() if
                      v}  # Remove False/empty values

        # Search for existing product template using ilike

        product_template = self.env['product.template'].search(
            ['|', ('name', '=', product_title),
             ('name', '=', product_title.lower())],
            limit=1)

        # Get or create category
        categ_id = self.get_or_create_category(category_name, category_cache)

        # Prepare product template data

        try:
            action = 'updated' if product_template else 'created'
            if product_template:
                template_data = {
                    'by_pass_variant_creation': True
                }
                # Update existing product template
                product_template.write(template_data)
                _logger.info(
                    f"Row {row_number}/{total_rows}: Updated product template - Name: {product_title}, Default Code: {default_code} (ID: {product_template.id})")
                _logger.debug(
                    f"Row {row_number}/{total_rows}: Updated product template: {product_title} (ID: {product_template.id}, S/N: {default_code})")
            else:
                template_data = {
                    'name': product_title,
                    'categ_id': categ_id,
                    'type': 'consu',
                    'purchase_ok': True,
                    'sale_ok': True,
                    'by_pass_variant_creation': True
                }

                # Create new product template
                product_template = self.env['product.template'].create(
                    template_data)
                _logger.info(
                    f"Row {row_number}/{total_rows}: Created product template - Name: {product_title}, Default Code: {default_code} (ID: {product_template.id})")
                _logger.debug(
                    f"Row {row_number}/{total_rows}: Created product template: {product_title} (ID: {product_template.id}, S/N: {default_code})")

            # Update attributes on product template
            self.update_product_template_attributes(product_template,
                                                    attributes,
                                                    attribute_cache,
                                                    value_cache)

            # Commit changes to the database
            self.env.cr.commit()
            _logger.debug(
                f"Row {row_number}/{total_rows}: Committed changes for product template: {product_template.name} (ID: {product_template.id})")

            elapsed_time = time.time() - start_time
            _logger.debug(
                f"Row {row_number}/{total_rows}: Processed product template {product_title} in {elapsed_time:.2f} seconds")

            return True, action

        except Exception as e:
            _logger.error(
                f"Row {row_number}/{total_rows}: Error processing product template {product_title} (S/N: {default_code}): {str(e)}")
            self.env.cr.rollback()  # Rollback on error to avoid partial commits
            return False, 'failed'

    def process_product(self, data, category_cache, attribute_cache,
                        value_cache, supplier_cache, row_number, total_rows):
        """Process a single row of CSV data to create a product.product if it doesn't exist."""
        start_time = time.time()
        product_title = self.parse_product_name(
            self.clean_value(data.get('Product Title')))
        default_code = self.clean_value(
            data.get('S/N')) or f"PROD-{uuid.uuid4().hex[:8]}"

        if not product_title:
            product_title = 'Empty Product'

        _logger.debug(
            f"Row {row_number}/{total_rows}: Processing product: {product_title} (S/N: {default_code})")

        # Check if product.product already exists
        existing_product = self.env['product.product'].search(
            [('default_code', '=', default_code)], limit=1)
        if existing_product:
            _logger.info(
                f"Row {row_number}/{total_rows}: Skipped existing product with default_code: {default_code} (ID: {existing_product.id})")
            return existing_product, 'skipped'

        # Extract fields
        supplier_name = self.clean_value(data.get('Supplier name'))
        status = self.clean_value(
            data.get('Status')).lower() if self.clean_value(
            data.get('Status')) else False
        sale_price = self.parse_sale_price(
            data.get('Sale price')) or 0.0  # Default to 0.0 if invalid
        category_name = self.clean_value(data.get('Product Category'))
        eu_field = self.clean_value(
            data.get('EU')).lower() if self.clean_value(
            data.get('EU')) else 'na'
        date_ordered = self.parse_date(
            self.clean_value(data.get('Date Ordered')))
        arrival_date = self.parse_date(
            self.clean_value(data.get('תאריך הגעה')))
        sold_date = self.parse_date(self.clean_value(data.get('Sold date')))

        # Map EU to source field
        source_map = {'eu': 'eu', 'br': 'br', '#n/a': 'na'}
        source = source_map.get(eu_field, 'na')

        # Extract attributes
        attributes = {
            'Top': self.clean_value(data.get('Top')),
            'Base Color': self.clean_value(data.get('Base Color')),
            'HL': self.clean_value(data.get('HL')),
            'Length': self.clean_value(data.get('Length (inch)')),
            'Layer': self.clean_value(data.get('Layer')),
            'Style': self.clean_value(data.get('Style')),
            'Size': self.clean_value(data.get('Size')),
        }
        attributes = {k: v for k, v in attributes.items() if
                      v}  # Remove False/empty values

        # Search for parent product template using ilike
        product_template = self.env['product.template'].search(
            ['|', ('name', '=', product_title),
             ('name', '=', product_title.lower())],
            limit=1)
        if not product_template:
            _logger.warning(
                f"Row {row_number}/{total_rows}: No product template found for {product_title} (S/N: {default_code})")
            return False, 'skipped'

        # Get or create category
        categ_id = self.get_or_create_category(category_name, category_cache)

        try:
            # Prepare product data
            product_data = {
                'product_tmpl_id': product_template.id,
                'default_code': default_code,
                'name': product_title,
                'lst_price': sale_price,
                'categ_id': categ_id,
                'source': source,
                'date_order': date_ordered,
                'arrival_date': arrival_date,
                'sold_date': sold_date,
            }

            # Only include status if it is not '#REF!'
            if status and status != '#ref!':
                product_data['status'] = status
            else:
                _logger.debug(
                    f"Row {row_number}/{total_rows}: Skipping status assignment for {product_title} (Status: {status})")

            # Create new product.product
            product = self.env['product.product'].create(product_data)
            _logger.info(
                f"Row {row_number}/{total_rows}: Created product.product - Name: {product_title}, Default Code: {default_code} (ID: {product.id}, Template ID: {product_template.id})")
            _logger.debug(
                f"Row {row_number}/{total_rows}: Created product.product: {product_title} (ID: {product.id}, S/N: {default_code})")

            # Assign attributes to product.product
            attribute_value_ids = []
            for attr_name, attr_value in attributes.items():
                attr_id, value_id = self.get_or_create_attribute(attr_name,
                                                                 attr_value,
                                                                 attribute_cache,
                                                                 value_cache)
                if not attr_id or not value_id:
                    _logger.debug(
                        f"Row {row_number}/{total_rows}: Skipping invalid attribute {attr_name} with value {attr_value} for product {product_title}")
                    continue
                # Find the corresponding product.template.attribute.value
                ptav = self.env['product.template.attribute.value'].search([
                    ('product_tmpl_id', '=', product_template.id),
                    ('attribute_id', '=', attr_id),
                    ('product_attribute_value_id', '=', value_id),
                ], limit=1)
                if ptav:
                    attribute_value_ids.append(ptav.id)
                    _logger.debug(
                        f"Row {row_number}/{total_rows}: Assigned attribute {attr_name} with value {attr_value} to product {product_title} (Product ID: {product.id}, PTAV ID: {ptav.id})")
                else:
                    _logger.warning(
                        f"Row {row_number}/{total_rows}: Could not find product.template.attribute.value for {attr_name}={attr_value} on template {product_title}")

            if attribute_value_ids:
                product.product_template_attribute_value_ids = [
                    (6, 0, attribute_value_ids)]
                _logger.debug(
                    f"Row {row_number}/{total_rows}: Updated product {product_title} with {len(attribute_value_ids)} attribute values (Product ID: {product.id})")

            # Handle supplier
            if supplier_name:
                vendor_id = self.get_or_create_supplier(supplier_name,
                                                        supplier_cache)
                if vendor_id:
                    # Check if supplier info already exists for this product and vendor
                    existing_supplier_info = self.env[
                        'product.supplierinfo'].search([
                        ('partner_id', '=', vendor_id),
                        ('product_id', '=', product.id),
                    ], limit=1)
                    if not existing_supplier_info:
                        self.env['product.supplierinfo'].create({
                            'partner_id': vendor_id,
                            'product_id': product.id,
                            'product_code': default_code,
                            'product_name': product_title,
                            # Added for traceability
                        })
                        _logger.debug(
                            f"Row {row_number}/{total_rows}: Added supplier {supplier_name} for product {product_title} (Product ID: {product.id}, Vendor ID: {vendor_id})")
                    else:
                        _logger.debug(
                            f"Row {row_number}/{total_rows}: Supplier {supplier_name} already linked to product {product_title} (Product ID: {product.id}, Vendor ID: {vendor_id})")

            # Commit changes to the database
            self.env.cr.commit()
            _logger.debug(
                f"Row {row_number}/{total_rows}: Committed changes for product: {product_title} (Product ID: {product.id}, Template ID: {product_template.id})")

            elapsed_time = time.time() - start_time
            _logger.debug(
                f"Row {row_number}/{total_rows}: Processed product {product_title} in {elapsed_time:.2f} seconds")

            return True, 'created'

        except Exception as e:
            _logger.error(
                f"Row {row_number}/{total_rows}: Error processing product {product_title} (S/N: {default_code}): {str(e)}")
            self.env.cr.rollback()  # Rollback on error to avoid partial commits
            return False, 'failed'

    @api.model
    def import_csv_data(self, csv_data):
        """Main method to import CSV data and process product templates, skipping first 5 rows."""
        start_time = time.time()
        _logger.info("Starting CSV data import for product templates")

        # Expected headers
        expected_headers = {'Product Title', 'S/N', 'Supplier name', 'Status',
                            'Sale price', 'Product Category', 'EU',
                            'Top', 'Base Color', 'HL', 'Length (inch)',
                            'Layer', 'Style', 'Size'}

        # Validate headers
        if not csv_data or not all(
                header in csv_data[0] for header in expected_headers):
            _logger.error(
                f"Invalid CSV headers. Expected: {expected_headers}, Found: {csv_data[0].keys() if csv_data else 'Empty'}")
            return

        # Skip first 5 rows
        csv_data = csv_data[5:] if len(csv_data) > 5 else []
        if not csv_data:
            _logger.warning("No data to process after skipping first 5 rows")
            return

        # Initialize caches and counters
        category_cache = {}
        attribute_cache = {}
        value_cache = {}
        stats = {'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        # Process rows in batches
        batch_size = 50  # Reduced batch size for more frequent commits
        total_rows = len(csv_data)
        _logger.info(
            f"Processing {total_rows} rows in batches of {batch_size}")

        for i in range(0, total_rows, batch_size):
            batch_start_time = time.time()
            batch = csv_data[i:i + batch_size]
            _logger.info(
                f"Processing batch {i // batch_size + 1} ({len(batch)} rows)")
            for idx, row in enumerate(batch, start=i + 1):
                success, action = self.process_product_template(row,
                                                                category_cache,
                                                                attribute_cache,
                                                                value_cache,
                                                                idx,
                                                                total_rows)
                if success:
                    stats[action] += 1
                else:
                    stats[action] += 1
            batch_elapsed_time = time.time() - batch_start_time
            _logger.info(
                f"Completed batch {i // batch_size + 1} in {batch_elapsed_time:.2f} seconds")

        total_elapsed_time = time.time() - start_time
        _logger.info(
            f"Completed CSV data import for product templates in {total_elapsed_time:.2f} seconds")
        _logger.info(
            f"Import summary: Created={stats['created']}, Updated={stats['updated']}, Skipped={stats['skipped']}, Failed={stats['failed']}")

    @api.model
    def cron_import_product_templates(self):
        """Cron job to process CSV data from a static file path for product templates."""
        start_time = time.time()
        _logger.info("Starting cron job to import product template CSV data")

        # Static CSV file path
        file_path = tools.misc.file_path(
            "bizzup_import_product/Product Data - Sheet.csv")

        # Check if file exists
        if not os.path.exists(file_path):
            _logger.error(f"CSV file not found at: {file_path}")
            return

        # Check file permissions
        if not os.access(file_path, os.R_OK):
            _logger.error(f"No read permissions for CSV file: {file_path}")
            return

        try:
            # Read and parse CSV file with UTF-8 encoding, handling BOM if present
            _logger.debug(f"Reading CSV file: {file_path}")
            with open(file_path, 'r', encoding='utf-8-sig') as csv_file:
                reader = csv.DictReader(csv_file)
                csv_data = [row for row in reader]

            if not csv_data:
                _logger.warning("CSV file is empty")
                return

            _logger.info(f"Read {len(csv_data)} rows from CSV file")
            # Import CSV data
            self.import_csv_data(csv_data)
            elapsed_time = time.time() - start_time
            _logger.info(
                f"Cron job for product templates completed successfully in {elapsed_time:.2f} seconds")

        except Exception as e:
            _logger.error(f"Cron job for product templates failed: {str(e)}")
            elapsed_time = time.time() - start_time
            _logger.info(
                f"Cron job for product templates terminated after {elapsed_time:.2f} seconds")
            raise

    @api.model
    def import_products_csv_data(self, csv_data):
        """Main method to import CSV data and create product.product records, skipping first 5 rows."""
        start_time = time.time()
        _logger.info("Starting CSV data import for products")

        # Expected headers
        expected_headers = {'Product Title', 'S/N', 'Supplier name', 'Status',
                            'Sale price', 'Product Category', 'EU',
                            'Top', 'Base Color', 'HL', 'Length (inch)',
                            'Layer', 'Style', 'Size', 'Date Ordered',
                            'תאריך הגעה', 'Sold date'}

        # Validate headers
        if not csv_data or not all(
                header in csv_data[0] for header in expected_headers):
            _logger.error(
                f"Invalid CSV headers. Expected: {expected_headers}, Found: {csv_data[0].keys() if csv_data else 'Empty'}")
            return

        # Skip first 5 rows
        csv_data = csv_data[5:] if len(csv_data) > 5 else []
        if not csv_data:
            _logger.warning("No data to process after skipping first 5 rows")
            return

        # Initialize caches and counters
        category_cache = {}
        attribute_cache = {}
        value_cache = {}
        supplier_cache = {}
        stats = {'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        # Process rows in batches
        batch_size = 50  # Reduced batch size for more frequent commits
        total_rows = len(csv_data)
        _logger.info(
            f"Processing {total_rows} rows in batches of {batch_size}")

        for i in range(0, total_rows, batch_size):
            batch_start_time = time.time()
            batch = csv_data[i:i + batch_size]
            _logger.info(
                f"Processing batch {i // batch_size + 1} ({len(batch)} rows)")
            for idx, row in enumerate(batch, start=i + 1):
                success, action = self.process_product(row, category_cache,
                                                       attribute_cache,
                                                       value_cache,
                                                       supplier_cache, idx,
                                                       total_rows)
                if success:
                    stats[action] += 1
                else:
                    stats[action] += 1
            batch_elapsed_time = time.time() - batch_start_time
            _logger.info(
                f"Completed batch {i // batch_size + 1} in {batch_elapsed_time:.2f} seconds")

        total_elapsed_time = time.time() - start_time
        _logger.info(
            f"Completed CSV data import for products in {total_elapsed_time:.2f} seconds")
        _logger.info(
            f"Import summary: Created={stats['created']}, Updated={stats['updated']}, Skipped={stats['skipped']}, Failed={stats['failed']}")

    @api.model
    def cron_create_products(self):
        """Cron job to process CSV data from a static file path for product.product creation."""
        self.env.cr.execute(
            "DROP INDEX IF EXISTS product_product_combination_unique;")

        start_time = time.time()
        _logger.info(
            "Starting cron job to create product.product from CSV data")

        # Static CSV file path
        file_path = tools.misc.file_path(
            "bizzup_import_product/Product Data - Sheet.csv")

        # Check if file exists
        if not os.path.exists(file_path):
            _logger.error(f"CSV file not found at: {file_path}")
            return

        # Check file permissions
        if not os.access(file_path, os.R_OK):
            _logger.error(f"No read permissions for CSV file: {file_path}")
            return

        try:
            # Read and parse CSV file with UTF-8 encoding, handling BOM if present
            _logger.debug(f"Reading CSV file: {file_path}")
            with open(file_path, 'r', encoding='utf-8-sig') as csv_file:
                reader = csv.DictReader(csv_file)
                csv_data = [row for row in reader]

            if not csv_data:
                _logger.warning("CSV file is empty")
                return

            _logger.info(f"Read {len(csv_data)} rows from CSV file")
            # Import CSV data for products
            self.import_products_csv_data(csv_data)
            elapsed_time = time.time() - start_time
            _logger.info(
                f"Cron job for product.product creation completed successfully in {elapsed_time:.2f} seconds")

        except Exception as e:
            _logger.error(
                f"Cron job for product.product creation failed: {str(e)}")
            elapsed_time = time.time() - start_time
            _logger.info(
                f"Cron job for product.product creation terminated after {elapsed_time:.2f} seconds")
            raise
