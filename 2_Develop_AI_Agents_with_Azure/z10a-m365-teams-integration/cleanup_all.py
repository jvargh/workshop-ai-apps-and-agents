"""
Lab-z10a - Cleanup All Resources
Removes all Azure resources created during the lab to avoid charges
"""

import subprocess
import sys
import json
from pathlib import Path

class ResourceCleanup:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.resource_group = None
        
    def print_header(self, title):
        """Print a formatted section header"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")
    
    def print_warning(self, message):
        """Print a warning message"""
        print(f"\n⚠️  WARNING: {message}\n")
    
    def get_deployment_info(self):
        """Get deployment info from azd"""
        print("🔍 Checking for deployed resources...\n")
        
        try:
            result = subprocess.run(
                ["azd", "env", "get-values"],
                capture_output=True,
                text=True,
                check=True
            )
            
            env_vars = {}
            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"')
            
            self.resource_group = env_vars.get('AZURE_RESOURCE_GROUP')
            
            if not self.resource_group:
                print("❌ No deployment found (resource group not set)")
                return False
            
            print(f"✅ Found deployment:")
            print(f"   Resource Group: {self.resource_group}")
            
            return True
            
        except subprocess.CalledProcessError:
            print("❌ No azd environment found")
            print("   Nothing to clean up")
            return False
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    def list_resources(self):
        """List all resources that will be deleted"""
        print("\n📋 Resources to be deleted:\n")
        
        try:
            result = subprocess.run(
                ["az", "resource", "list", "--resource-group", self.resource_group],
                capture_output=True,
                text=True,
                check=True
            )
            
            resources = json.loads(result.stdout)
            
            if not resources:
                print("   No resources found")
                return True
            
            resource_types = {}
            for resource in resources:
                rtype = resource.get('type', '').split('/')[-1]
                rname = resource.get('name', 'Unknown')
                
                if rtype not in resource_types:
                    resource_types[rtype] = []
                resource_types[rtype].append(rname)
            
            for rtype, names in sorted(resource_types.items()):
                print(f"   • {rtype} ({len(names)} resource{'s' if len(names) > 1 else ''})")
                for name in names:
                    print(f"      - {name}")
            
            print(f"\n   Total: {len(resources)} resources")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Could not list resources: {e.stderr}")
            return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
    
    def estimate_cost_savings(self):
        """Show potential cost savings from cleanup"""
        print("\n💰 Cost Savings:\n")
        print("   By cleaning up resources, you avoid ongoing charges:")
        print("   • Azure OpenAI: ~$0.50/day")
        print("   • Azure AI Search: ~$0.25-0.50/hour")
        print("   • Container Registry: ~$0.10/day")
        print("   • Application Insights: Free tier (no charge)")
        print()
        print("   Estimated savings: ~$1-2/day if left running")
        print()
    
    def cleanup_with_azd(self):
        """Use azd down to delete everything"""
        print("\n🗑️  Cleaning up with Azure Developer CLI...\n")
        
        self.print_warning("This will DELETE ALL resources in the resource group!")
        print("This includes:")
        print("   • AI Foundry project")
        print("   • Azure OpenAI deployment")
        print("   • Azure AI Search service")
        print("   • Container Registry")
        print("   • Application Insights")
        print("   • All associated resources")
        print()
        
        response = input("Are you sure you want to delete everything? Type 'yes' to confirm: ")
        
        if response.lower() != 'yes':
            print("\n❌ Cleanup cancelled")
            return False
        
        print("\n🚀 Running azd down...\n")
        print("⏱️  This may take 3-5 minutes...\n")
        
        try:
            result = subprocess.run(
                ["azd", "down", "--force", "--purge"],
                check=True
            )
            
            print("\n✅ All resources deleted successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Cleanup failed: {e}")
            print("\nYou can try manual cleanup:")
            print(f"   az group delete --name {self.resource_group} --yes --no-wait")
            return False
    
    def verify_cleanup(self):
        """Verify resources were deleted"""
        print("\n✅ Verifying cleanup...\n")
        
        try:
            result = subprocess.run(
                ["az", "group", "exists", "--name", self.resource_group],
                capture_output=True,
                text=True,
                check=True
            )
            
            exists = result.stdout.strip().lower() == 'true'
            
            if exists:
                print(f"⚠️  Resource group '{self.resource_group}' still exists")
                print("   It may be in deletion process (takes a few minutes)")
                print("\n   Check status with:")
                print(f"   az group show --name {self.resource_group}")
            else:
                print(f"✅ Resource group '{self.resource_group}' deleted")
                print("   All resources removed successfully!")
            
            return not exists
            
        except subprocess.CalledProcessError:
            print("✅ Resource group not found (successfully deleted)")
            return True
        except Exception as e:
            print(f"⚠️  Could not verify: {str(e)}")
            return False
    
    def manual_cleanup_instructions(self):
        """Provide manual cleanup instructions"""
        print("\n" + "=" * 70)
        print("  Manual Cleanup Instructions")
        print("=" * 70 + "\n")
        
        print("If automatic cleanup failed, you can delete resources manually:\n")
        
        print("1. Delete Resource Group (removes everything):")
        print(f"   az group delete --name {self.resource_group} --yes --no-wait")
        print()
        
        print("2. Or delete via Azure Portal:")
        print("   • Go to: https://portal.azure.com")
        print("   • Navigate to Resource Groups")
        print(f"   • Find: {self.resource_group}")
        print("   • Click 'Delete resource group'")
        print("   • Type the resource group name to confirm")
        print()
        
        print("3. Verify deletion (after 5-10 minutes):")
        print(f"   az group exists --name {self.resource_group}")
        print("   Should return: false")
        print()
    
    def teams_app_cleanup(self):
        """Instructions for removing Teams app"""
        print("\n" + "=" * 70)
        print("  Microsoft Teams App Cleanup")
        print("=" * 70 + "\n")
        
        print("If you published your agent to Teams, remove it manually:\n")
        
        print("1. Open Microsoft Teams")
        print("2. Go to 'Apps' in the left sidebar")
        print("3. Click 'Manage your apps' (bottom left)")
        print("4. Find your custom app")
        print("5. Click the '...' menu → 'Uninstall'")
        print("6. Confirm deletion")
        print()
        
        print("Note: The Azure Bot Service will be deleted with the resource group")
        print()
    
    def cleanup_local_files(self):
        """Option to clean up local configuration files"""
        print("\n🗑️  Local File Cleanup (Optional)\n")
        
        print("Do you want to remove local configuration files?")
        print("This includes:")
        print("   • .azure/ folder (azd environment)")
        print("   • .env file (connection strings)")
        print("   • azure.yaml (project config)")
        print()
        
        response = input("Remove local config files? (y/N): ")
        
        if response.lower() == 'y':
            files_to_remove = [
                self.project_dir / ".azure",
                self.project_dir / ".env",
                self.project_dir / "azure.yaml"
            ]
            
            for file_path in files_to_remove:
                try:
                    if file_path.exists():
                        if file_path.is_dir():
                            import shutil
                            shutil.rmtree(file_path)
                        else:
                            file_path.unlink()
                        print(f"   ✅ Removed: {file_path.name}")
                except Exception as e:
                    print(f"   ⚠️  Could not remove {file_path.name}: {str(e)}")
            
            print("\n✅ Local files cleaned up")
        else:
            print("\n   Keeping local files (you can delete manually later)")
    
    def show_summary(self):
        """Show cleanup summary"""
        print("\n" + "=" * 70)
        print("  Cleanup Complete! 🎉")
        print("=" * 70 + "\n")
        
        print("✅ What was cleaned up:")
        print("   • All Azure resources deleted")
        print("   • Resource group removed")
        print("   • No more charges accruing")
        print()
        
        print("📝 What to do next:")
        print("   • Verify in Azure Portal that resources are gone")
        print("   • Remove Teams app if you installed it")
        print("   • Check your Azure billing to confirm no charges")
        print()
        
        print("💡 To deploy again:")
        print("   • Run: python deploy_helper.py")
        print("   • Follow the deployment wizard")
        print()
    
    def run(self):
        """Run the cleanup workflow"""
        self.print_header("Lab-z10a: Resource Cleanup")
        
        print("This script will help you clean up all Azure resources created during Lab-z10a.")
        print("\n⚠️  IMPORTANT: This will DELETE all deployed resources and cannot be undone!")
        print()
        
        # Step 1: Get deployment info
        if not self.get_deployment_info():
            print("\nNo resources found to clean up. You're all set! ✅")
            return True
        
        # Step 2: List resources
        if not self.list_resources():
            print("\n⚠️  Could not list resources, but will proceed with cleanup")
        
        # Step 3: Show cost savings
        self.estimate_cost_savings()
        
        # Step 4: Confirm and cleanup
        success = self.cleanup_with_azd()
        
        if success:
            # Step 5: Verify
            self.verify_cleanup()
            
            # Step 6: Local files
            self.cleanup_local_files()
            
            # Step 7: Teams cleanup instructions
            self.teams_app_cleanup()
            
            # Step 8: Summary
            self.show_summary()
        else:
            # Show manual instructions if automatic failed
            self.manual_cleanup_instructions()
            self.teams_app_cleanup()
        
        return success

def main():
    print("[Mode] Destructive deployment cleanup. Do not run this to reset the local Search/chat lab or remove shared resources.", flush=True)
    print("\n⚠️  WARNING: This script will DELETE all Azure resources!")
    print("Make sure you've saved any important data before proceeding.\n")
    
    response = input("Ready to proceed with cleanup? (y/N): ")
    
    if response.lower() != 'y':
        print("\nCleanup cancelled. Resources remain deployed.")
        print("Run this script again when you're ready to clean up.")
        return
    
    cleanup = ResourceCleanup()
    cleanup.run()

if __name__ == "__main__":
    main()
