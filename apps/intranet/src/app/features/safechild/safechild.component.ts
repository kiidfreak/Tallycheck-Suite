import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonComponent, IconComponent, ToastService } from '@omni/ui';
import { AuthService } from '@omni/auth';
import { SafeChildService, Child, Guardian, DropOffResponse, VerificationResponse } from './safechild.service';

@Component({
  selector: 'app-safechild',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonComponent, IconComponent],
  templateUrl: './safechild.component.html',
  styleUrls: ['./safechild.component.scss']
})
export class SafechildComponent implements OnInit {
  private readonly safeChildService = inject(SafeChildService);
  readonly auth = inject(AuthService);
  private readonly toastService = inject(ToastService);

  readonly children = signal<Child[]>([]);
  readonly loading = signal(false);

  // Filter/Search states
  readonly searchQuery = signal('');
  readonly selectedGroup = signal('All');

  // Drop-off form drawer state
  readonly isDropOffOpen = signal(false);
  readonly activeChildForDropOff = signal<Child | null>(null);
  readonly selectedGuardianId = signal<string>('');
  readonly selectedLocation = signal<string>('Ezra Building');
  readonly dropOffLoading = signal(false);

  readonly locations = [
    'Ezra Building',
    'Facility Centre',
    'Main Tent',
    'Church Gate / Sanctuary Entrance',
    'Other Location'
  ];

  // Success receipt after drop-off
  readonly activeReceipt = signal<DropOffResponse | null>(null);

  // Verification Gate state
  readonly isVerifyPanelOpen = signal(false);
  readonly verificationCode = signal('');
  readonly verificationLoading = signal(false);
  readonly activeVerificationResult = signal<VerificationResponse | null>(null);

  readonly my_children = computed(() => {
    const user = this.auth.user();
    const userName = (user?.name || user?.first_name || 'Grace').toLowerCase();
    
    const myKids = this.children().filter(c => 
      c.guardians.some(g => g.name.toLowerCase().includes(userName) || userName.includes(g.name.toLowerCase().split(' ')[0]))
    );

    return myKids.length ? myKids : this.children().slice(0, 2);
  });

  ngOnInit() {
    this.loadChildren();
  }

  loadChildren() {
    this.loading.set(true);
    this.safeChildService.getChildren().subscribe({
      next: (res) => {
        this.children.set(res);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }

  getGroups(): string[] {
    const groups = new Set<string>();
    this.children().forEach(c => groups.add(c.group_name));
    return ['All', ...Array.from(groups)];
  }

  getFilteredChildren(): Child[] {
    // If user is a parent / guardian (or does not have safechild:drop_off / manage_children),
    // ONLY return their own attached children!
    if (!this.auth.can('safechild:drop_off') && !this.auth.can('safechild:manage_children')) {
      return this.my_children();
    }

    return this.children().filter(c => {
      const matchesSearch = c.name.toLowerCase().includes(this.searchQuery().toLowerCase()) ||
                            c.guardians.some(g => g.name.toLowerCase().includes(this.searchQuery().toLowerCase()));
      const matchesGroup = this.selectedGroup() === 'All' || c.group_name === this.selectedGroup();
      return matchesSearch && matchesGroup;
    });
  }

  onQuickSelectChild(childId: string) {
    if (!childId) return;
    const child = this.children().find(c => c.id === childId);
    if (child) {
      this.openDropOff(child);
    }
  }

  openDropOff(child: Child) {
    this.activeChildForDropOff.set(child);
    const primary = child.guardians.find(g => g.is_primary);
    this.selectedGuardianId.set(primary ? primary.id : (child.guardians[0]?.id || ''));
    this.isDropOffOpen.set(true);
  }

  closeDropOff() {
    this.isDropOffOpen.set(false);
    this.activeChildForDropOff.set(null);
    this.selectedGuardianId.set('');
  }

  submitDropOff() {
    const child = this.activeChildForDropOff();
    if (!child) return;

    this.dropOffLoading.set(true);
    this.safeChildService.logDropOff(child.id, this.selectedGuardianId() || undefined).subscribe({
      next: (res) => {
        this.activeReceipt.set(res);
        this.dropOffLoading.set(false);
        this.closeDropOff();
        this.loadChildren();
        this.toastService.show('Drop-off registered successfully', 'success');
      },
      error: (err) => {
        this.dropOffLoading.set(false);
        this.toastService.show(err.error?.message || 'Failed to complete drop-off', 'error');
      }
    });
  }

  closeReceipt() {
    this.activeReceipt.set(null);
  }

  openVerifyPanel() {
    this.verificationCode.set('');
    this.activeVerificationResult.set(null);
    this.isVerifyPanelOpen.set(true);
  }

  closeVerifyPanel() {
    this.isVerifyPanelOpen.set(false);
    this.verificationCode.set('');
    this.activeVerificationResult.set(null);
  }

  submitVerification() {
    const code = this.verificationCode().trim();
    if (!code) {
      this.toastService.show('Please enter a PIN or scan a QR code', 'error');
      return;
    }

    this.verificationLoading.set(true);
    this.safeChildService.verifyPickup(code).subscribe({
      next: (res) => {
        this.activeVerificationResult.set(res);
        this.verificationLoading.set(false);
        this.loadChildren();
        this.toastService.show('Pickup verified successfully!', 'success');
      },
      error: (err) => {
        this.verificationLoading.set(false);
        this.toastService.show(err.error?.message || 'Verification failed', 'error');
      }
    });
  }
}
