import argparse
import hashlib

from db_connection import get_connection, close_connection


def main():
    parser = argparse.ArgumentParser(description='Reset a faculty password (dev utility).')
    parser.add_argument('--email', required=True, help='Faculty email')
    parser.add_argument('--password', default='faculty123', help='New password')
    args = parser.parse_args()

    password_hash = hashlib.sha256(args.password.encode()).hexdigest()

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE faculty SET password_hash=%s WHERE email=%s', (password_hash, args.email))
        conn.commit()
        print(f'Updated rows: {cursor.rowcount}')
        if cursor.rowcount == 0:
            print('No faculty found for that email.')
        else:
            print('Password reset successful.')
    finally:
        close_connection(conn)


if __name__ == '__main__':
    main()
