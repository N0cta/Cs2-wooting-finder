#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CS2 Wooting Detector - Version EXE tout-en-un
Un seul lancement suffit : Installation automatique + Surveillance permanente
"""

import time
import psutil
import tkinter as tk
from tkinter import messagebox
import threading
import sys
import os
import subprocess
from pathlib import Path
import logging
import winreg
import tempfile
import atexit
import signal

# Configuration
PROCESS_NAME = "cs2.exe"
CHECK_INTERVAL = 2
APP_NAME = "CS2WootingDetector"
MUTEX_NAME = "CS2WootingDetector_SingleInstance"


class SingleInstance:
    """Assure qu'une seule instance du programme tourne"""

    def __init__(self, mutex_name):
        self.mutex_name = mutex_name
        self.mutex_file = Path(tempfile.gettempdir()) / f"{mutex_name}.lock"

    def __enter__(self):
        try:
            if self.mutex_file.exists():
                # Vérifier si le processus existe encore
                try:
                    with open(self.mutex_file, 'r') as f:
                        old_pid = int(f.read().strip())

                    # Si le processus n'existe plus, supprimer le fichier
                    if not psutil.pid_exists(old_pid):
                        self.mutex_file.unlink()
                    else:
                        return False  # Instance déjà en cours
                except:
                    self.mutex_file.unlink()  # Fichier corrompu

            # Créer le fichier mutex avec notre PID
            with open(self.mutex_file, 'w') as f:
                f.write(str(os.getpid()))

            return True
        except:
            return False

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.mutex_file.exists():
                self.mutex_file.unlink()
        except:
            pass


class CS2WootingDetector:
    def __init__(self):
        self.running = True
        self.cs2_detected = False
        self.installed = False
        self.setup_logging()

    def setup_logging(self):
        """Configure le système de logs"""
        try:
            log_dir = Path.home() / "AppData" / "Local" / APP_NAME
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / "detector.log"

            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler() if not getattr(sys, 'frozen', False) else logging.NullHandler()
                ]
            )
        except Exception as e:
            print(f"Erreur configuration logging: {e}")

    def is_process_running(self, process_name):
        """Vérifie si un processus est en cours d'exécution"""
        try:
            for process in psutil.process_iter(['name']):
                if process.info['name'] and process.info['name'].lower() == process_name.lower():
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        return False

    def show_wooting_alert(self):
        """Affiche l'alerte pour désactiver Wooting"""

        def create_alert_window():
            try:
                root = tk.Tk()
                root.withdraw()
                root.lift()
                root.attributes('-topmost', True)
                root.after(100, lambda: root.focus_force())

                message = (
                    "🎮 Counter-Strike 2 détecté !\n\n"
                    "⚠️  ACTION REQUISE  ⚠️\n\n"
                    "Avant de rejoindre une partie en ligne :\n"
                    "• Désactivez votre clavier Wooting\n"
                    "• Ou utilisez le mode de compatibilité\n\n"
                    "Ceci évite les problèmes de détection anti-triche.\n\n"
                    "Cliquez OK pour continuer."
                )

                messagebox.showwarning("CS2 - Rappel Wooting", message)
                root.destroy()

            except Exception as e:
                logging.error(f"Erreur affichage alerte: {e}")

        alert_thread = threading.Thread(target=create_alert_window, daemon=True)
        alert_thread.start()

    def add_to_startup(self):
        """Ajoute le programme au démarrage Windows"""
        try:
            if not getattr(sys, 'frozen', False):
                return False  # Ne fonctionne qu'avec l'EXE

            exe_path = os.path.abspath(sys.executable)
            logging.info(f"Installation au démarrage: {exe_path}")

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )

            startup_command = f'"{exe_path}" --daemon'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, startup_command)
            winreg.CloseKey(key)

            logging.info("✅ Installation au démarrage réussie")
            return True

        except Exception as e:
            logging.error(f"❌ Erreur installation démarrage: {e}")
            return False

    def is_in_startup(self):
        """Vérifie si le programme est dans le démarrage"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )

            value, _ = winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True

        except FileNotFoundError:
            return False
        except Exception:
            return False

    def show_installation_success(self):
        """Affiche le message de succès d'installation"""

        def show_success():
            try:
                root = tk.Tk()
                root.title("CS2 Wooting Detector - Installation")
                root.geometry("450x350")
                root.resizable(False, False)

                # Centrer la fenêtre
                root.update_idletasks()
                x = (root.winfo_screenwidth() // 2) - (450 // 2)
                y = (root.winfo_screenheight() // 2) - (350 // 2)
                root.geometry(f"450x350+{x}+{y}")

                # Style
                bg_color = "#f0f0f0"
                root.configure(bg=bg_color)

                # Titre
                title_label = tk.Label(
                    root,
                    text="✅ Installation Réussie !",
                    font=("Arial", 18, "bold"),
                    fg="#4CAF50",
                    bg=bg_color
                )
                title_label.pack(pady=20)

                # Message principal
                message = tk.Text(
                    root,
                    height=12,
                    width=50,
                    font=("Arial", 11),
                    wrap=tk.WORD,
                    bg="white",
                    relief="flat",
                    padx=15,
                    pady=15
                )

                success_text = """🎮 CS2 Wooting Detector est maintenant installé !

✅ Démarrage automatique configuré
✅ Surveillance en arrière-plan active
✅ Alertes automatiques lors du lancement de CS2

COMMENT ÇA FONCTIONNE :
• Le programme tourne en permanence en arrière-plan
• Dès que CS2 se lance, une alerte apparaît
• Rappel automatique de désactiver Wooting
• Aucune action supplémentaire requise

LOGS ET INFORMATIONS :
• Logs disponibles dans vos documents
• Le programme redémarre avec Windows
• Très faible impact sur les performances

Vous pouvez fermer cette fenêtre.
Le programme continuera à fonctionner en arrière-plan !"""

                message.insert(tk.END, success_text)
                message.configure(state='disabled')
                message.pack(pady=10, padx=20)

                # Bouton de fermeture
                close_btn = tk.Button(
                    root,
                    text="OK - Continuer en arrière-plan",
                    command=root.destroy,
                    bg="#4CAF50",
                    fg="white",
                    font=("Arial", 12, "bold"),
                    pady=8
                )
                close_btn.pack(pady=15)

                # Auto-fermeture après 15 secondes
                root.after(15000, root.destroy)

                root.mainloop()

            except Exception as e:
                logging.error(f"Erreur affichage succès: {e}")

        success_thread = threading.Thread(target=show_success, daemon=True)
        success_thread.start()
        success_thread.join()  # Attendre que la fenêtre se ferme

    def perform_installation(self):
        """Effectue l'installation complète"""
        logging.info("=== DÉBUT DE L'INSTALLATION ===")

        # Vérifier si déjà installé
        if self.is_in_startup():
            logging.info("Programme déjà installé - passage en mode surveillance")
            return True

        # Installation au démarrage
        success = self.add_to_startup()
        if success:
            self.installed = True
            logging.info("✅ Installation terminée avec succès")

            # Afficher le message de succès
            self.show_installation_success()
            return True
        else:
            logging.error("❌ Échec de l'installation")
            return False

    def monitor_processes(self):
        """Surveillance continue des processus"""
        logging.info("=== SURVEILLANCE ACTIVE ===")
        consecutive_errors = 0
        max_errors = 5

        while self.running:
            try:
                cs2_running = self.is_process_running(PROCESS_NAME)

                if cs2_running and not self.cs2_detected:
                    logging.info("🎮 CS2 détecté ! Affichage de l'alerte Wooting.")
                    self.cs2_detected = True
                    self.show_wooting_alert()

                elif not cs2_running and self.cs2_detected:
                    logging.info("CS2 fermé - surveillance continue.")
                    self.cs2_detected = False

                consecutive_errors = 0
                time.sleep(CHECK_INTERVAL)

            except Exception as e:
                consecutive_errors += 1
                logging.error(f"Erreur surveillance (tentative {consecutive_errors}/{max_errors}): {e}")

                if consecutive_errors >= max_errors:
                    logging.critical("Trop d'erreurs consécutives - arrêt de la surveillance")
                    break

                time.sleep(CHECK_INTERVAL * 2)

        logging.info("=== SURVEILLANCE TERMINÉE ===")

    def run_daemon(self):
        """Mode daemon - surveillance silencieuse"""
        logging.info("=== MODE DAEMON DÉMARRÉ ===")
        try:
            self.monitor_processes()
        except Exception as e:
            logging.error(f"Erreur en mode daemon: {e}")

    def stop(self):
        """Arrête la surveillance"""
        self.running = False


def cleanup_on_exit():
    """Nettoyage à la fermeture"""
    try:
        mutex_file = Path(tempfile.gettempdir()) / f"{MUTEX_NAME}.lock"
        if mutex_file.exists():
            mutex_file.unlink()
    except:
        pass


def signal_handler(signum, frame):
    """Gestionnaire de signaux pour arrêt propre"""
    logging.info("Signal d'arrêt reçu")
    sys.exit(0)


def main():
    """Fonction principale - Installation ou surveillance selon le contexte"""

    # Configuration des signaux et nettoyage
    atexit.register(cleanup_on_exit)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Vérifier qu'une seule instance tourne
    with SingleInstance(MUTEX_NAME) as single:
        if not single:
            logging.info("Une instance est déjà en cours d'exécution")
            return

        detector = CS2WootingDetector()

        try:
            # Mode daemon (lancé au démarrage avec --daemon)
            if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
                detector.run_daemon()
                return

            # Premier lancement ou lancement manuel
            if not detector.is_in_startup():
                logging.info("🚀 PREMIER LANCEMENT - Installation automatique")

                # Effectuer l'installation
                if detector.perform_installation():
                    # Après installation réussie, continuer en mode surveillance
                    logging.info("Installation terminée - Démarrage de la surveillance")
                    detector.monitor_processes()
                else:
                    logging.error("Installation échouée")
                    if getattr(sys, 'frozen', False):
                        root = tk.Tk()
                        root.withdraw()
                        messagebox.showerror(
                            "Erreur d'installation",
                            "L'installation automatique a échoué.\n\n"
                            "Essayez de lancer le programme en tant qu'administrateur."
                        )
                        root.destroy()
            else:
                # Déjà installé - mode surveillance normale
                logging.info("Programme déjà installé - Mode surveillance")
                detector.monitor_processes()

        except KeyboardInterrupt:
            logging.info("Arrêt demandé par l'utilisateur")
        except Exception as e:
            logging.error(f"Erreur fatale: {e}")
        finally:
            detector.stop()


if __name__ == "__main__":
    # En mode EXE, cacher la console
    if getattr(sys, 'frozen', False):
        try:
            import ctypes

            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass

    main()
