import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PendingComponent } from './pending.component';
import { AuthService } from '@omni/auth';
import { Component, Input } from '@angular/core';
import { IconComponent } from '@omni/ui';

@Component({
  // eslint-disable-next-line @angular-eslint/component-selector
  selector: 'omni-icon',
  standalone: true,
  template: '<span>mock icon</span>'
})
class MockIconComponent {
  @Input() name!: string;
}

describe('PendingComponent', () => {
  let component: PendingComponent;
  let fixture: ComponentFixture<PendingComponent>;
  let mockAuthService: { fetch_db_profile: jest.Mock };

  beforeEach(async () => {
    mockAuthService = {
      fetch_db_profile: jest.fn()
    };

    await TestBed.configureTestingModule({
      imports: [PendingComponent],
      providers: [
        { provide: AuthService, useValue: mockAuthService }
      ]
    })
    .overrideComponent(PendingComponent, {
      remove: { imports: [IconComponent] },
      add: { imports: [MockIconComponent] } // Mock the lucide icons
    })
    .compileComponents();

    fixture = TestBed.createComponent(PendingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the pending component successfully', () => {
    expect(component).toBeTruthy();
  });

  it('should trigger AuthService.fetch_db_profile() to check approval status when refreshed', () => {
    component.refresh();
    
    // Verify our fake AuthService was triggered
    expect(mockAuthService.fetch_db_profile).toHaveBeenCalledTimes(1);
  });
});
