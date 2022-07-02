import argparse
import asyncio
import logging

from millegrilles_messages.backup.Backup import main as backup_main
from millegrilles_messages.backup.Restaurer import main as restaurer_main
from millegrilles_messages.backup.DemarrerBackup import main as demarrer_backup


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Demarrer une application midcompte/certissuer/utils de MilleGrilles")
    parser.add_argument(
        '--verbose', action="store_true", required=False,
        help="Active le logging maximal"
    )

    subparsers = parser.add_subparsers(dest='command', required=True, help="Commandes")

    # Demarrer un backup de transactions
    subparser_demarrer = subparsers.add_parser('demarrer', help='Declencher un backup de transactions')
    subparser_demarrer.add_argument('--complet', action='store_true', required=False,
                                    help='Repertoire source du backup')

    # Subparser backup
    subparser_backup = subparsers.add_parser('backup', help='Backup de fichiers')
    subparser_backup.add_argument('--source', default='/var/opt/millegrilles_backup',
                                  help='Repertoire source du backup')
    subparser_backup.add_argument('--dest', default='/var/opt/millegrilles_backup/_ARCHIVES',
                                  help='Repertoire destination du backup')
    subparser_backup.add_argument('--ca', default='/var/opt/millegrilles/configuration/pki.millegrille.cert',
                                  help='Certificat de MilleGrille')

    # Subparser restaurer
    subparser_restaurer = subparsers.add_parser('restaurer', help='Restaurer archive')
    subparser_restaurer.add_argument('--cleca', required=True, help='Path/URL du JSON de cle de millegrille')
    subparser_restaurer.add_argument('--workpath', default='/tmp/millegrilles_restaurer',
                                     help='Path/URL de travail pour l''extraction')
    subparser_restaurer.add_argument('--archive', required=False, help='Path/URL de fichier d''archive')
    subparser_restaurer.add_argument('--transactions', action='store_true', required=False, help='Restaurer les transactions avec MQ')
    subparser_restaurer.add_argument('--rechiffrer', action='store_true', required=False,
                                     help='Rechiffrer domaine MaitreDesCles')

    args = parser.parse_args()
    adjust_logging(args)

    return args


def adjust_logging(args: argparse.Namespace):
    if args.verbose is True:
        loggers = [__name__, 'millegrilles_messages']
        for log in loggers:
            logging.getLogger(log).setLevel(logging.DEBUG)


async def demarrer(args: argparse.Namespace):
    command = args.command

    if command == 'demarrer':
        await demarrer_backup(args.complet)
    elif command == 'backup':
        await backup_main(args.source, args.dest, args.ca)
    elif command == 'restaurer':
        await restaurer_main(args.archive, args.workpath, args.cleca,
                             transactions=args.transactions, rechiffrer=args.rechiffrer)
    else:
        raise ValueError('non supporte')


def main():
    """
    Methode d'execution de l'application
    :return:
    """
    logging.basicConfig()
    logging.getLogger(__name__).setLevel(logging.INFO)

    args = parse()
    asyncio.run(demarrer(args))


if __name__ == '__main__':
    main()
