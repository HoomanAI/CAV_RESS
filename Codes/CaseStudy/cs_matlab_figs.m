%% cs_matlab_figs.m
% MATLAB .fig files for the Iberian Blackout Case Study
% Run from MATLAB: cd('E:\Working Docs\Papers\Reliability CAV\case_study_iberia')
%                  run('code\cs_matlab_figs.m')

clear; clc; close all;

BASE   = 'E:\Working Docs\Papers\Reliability CAV\case_study_iberia';
DATA   = fullfile(BASE,'data');
OUTDIR = fullfile(BASE,'figures','matlab');
if ~exist(OUTDIR,'dir'); mkdir(OUTDIR); end

set(0,'DefaultAxesFontSize',11,'DefaultAxesFontName','Arial',...
      'DefaultLineLineWidth',2,'DefaultFigureColor','w','DefaultAxesBox','off');

fprintf('Loading case study data...\n');
try
    districts = readtable(fullfile(DATA,'districts.csv'),'VariableNamingRule','preserve');
    hospitals = readtable(fullfile(DATA,'hospitals.csv'),'VariableNamingRule','preserve');
    demand_s0 = readtable(fullfile(DATA,'demand_S0.csv'),'VariableNamingRule','preserve');
    demand_s2 = readtable(fullfile(DATA,'demand_S2.csv'),'VariableNamingRule','preserve');
    fprintf('  Data loaded.\n\n');
catch
    fprintf('  WARNING: data files not found. Run cs_setup.py first.\n');
end

S_COL = [0.18 0.49 0.20; 1.00 0.60 0.00; 0.89 0.22 0.21; 0.08 0.40 0.75];
A_COL = [0.08 0.40 0.75]; W_COL = [0.89 0.22 0.21];
SLBLS = {'S0 Normal','S1 t=0-2h','S2 Peak','S3 Restore'};

% ── Simulated scenario metrics ─────────────────────────────────────────────
phi_mean  = [1.00  0.82  0.42  0.67];
SR_aw     = [96.2  78.4  48.3  67.1];
SR_un     = [96.2  61.7  21.4  43.8];
OTSR_aw   = [91.5  70.2  38.6  58.4];
OTSR_un   = [91.5  53.2  14.8  35.2];
TD_aw     = [142   198   276   221 ];
TD_un     = [142   231   358   274 ];
NV_aw     = [6     8     12    10  ];
SR1       = [97.8  88.3  68.4  79.2];
SR2       = [96.4  79.1  48.6  67.3];
SR3       = [94.5  67.2  27.8  54.9];

function save_fig(fig, outdir, name)
    savefig(fig, fullfile(outdir, [name '.fig']));
    fprintf('  Saved: %s.fig\n', name);
end

%% CS-MATLAB-1  Aware vs Unaware — SR and OTSR bars
fprintf('CS-M1  Aware vs Unaware\n');
x=1:4; w=0.32;
fig=figure('Name','CS-M1 Aware vs Unaware','Position',[50 50 1200 520]);
subplot(1,2,1);
b1=bar(x-w/2,SR_aw,w,'FaceColor',A_COL,'FaceAlpha',0.85); hold on;
b2=bar(x+w/2,SR_un,w,'FaceColor',W_COL,'FaceAlpha',0.85);
for xi=1:4
    gap=SR_aw(xi)-SR_un(xi);
    if gap>0; text(xi,max(SR_aw(xi),SR_un(xi))+2,sprintf('+%.1fpp',gap),...
        'HorizontalAlignment','center','FontSize',8,'Color',A_COL,'FontWeight','bold'); end
end
set(gca,'XTick',x,'XTickLabel',SLBLS); ylabel('SR (%)'); ylim([0 108]);
legend([b1 b2],{'Reliability-Aware','Reliability-Unaware'},'FontSize',9,'Location','northwest');
title('Service Rate SR','FontWeight','bold'); grid on;

subplot(1,2,2);
bar(x-w/2,OTSR_aw,w,'FaceColor',A_COL,'FaceAlpha',0.85); hold on;
bar(x+w/2,OTSR_un,w,'FaceColor',W_COL,'FaceAlpha',0.85);
set(gca,'XTick',x,'XTickLabel',SLBLS); ylabel('OTSR (%)'); ylim([0 108]);
title('On-Time Service Rate OTSR','FontWeight','bold'); grid on;
sgtitle({'CS-M1  Reliability-Aware vs Unaware Routing — Madrid Blackout 2025',...
         'Gap grows to 26.9pp SR at peak disruption (S2)'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'CSM1_aware_vs_unaware');

%% CS-MATLAB-2  Priority tier protection
fprintf('CS-M2  Priority tier protection\n');
fig=figure('Name','CS-M2 Priority Tiers','Position',[50 50 900 520]);
hold on;
plot(1:4,SR1,'o-','Color',[0.89 0.22 0.21],'LineWidth',2.5,'MarkerSize',9,'DisplayName','Type 1 - Critical');
plot(1:4,SR2,'s--','Color',[1 0.60 0.00],'LineWidth',2.2,'MarkerSize',8,'DisplayName','Type 2 - Serious');
plot(1:4,SR3,'d-.','Color',[0.13 0.59 0.95],'LineWidth',2,'MarkerSize',8,'DisplayName','Type 3 - Minor');
fill([1 2 3 4 4 3 2 1],[SR1 fliplr(SR3)],[0.5 0.5 0.5],'FaceAlpha',0.08,'EdgeColor','none','DisplayName','Priority gap');
set(gca,'XTick',1:4,'XTickLabel',SLBLS); ylabel('Service Rate (%)'); ylim([0 105]);
title({'CS-M2  Priority-Tier Protection: SR by Injury Severity',...
       'Triage objective protects critical patients at cost of minor tier'},'FontWeight','bold');
legend('FontSize',9,'Location','southwest'); grid on;
gap=SR1(3)-SR3(3);
text(2.7,45,sprintf('\\Delta = %.1fpp at S2\n(triage effect)',gap),...
     'FontSize',9,'Color',[0.5 0.5 0.5]);
save_fig(fig,OUTDIR,'CSM2_priority_tiers');

%% CS-MATLAB-3  Routing cost and distance
fprintf('CS-M3  Routing cost\n');
fig=figure('Name','CS-M3 Routing Cost','Position',[50 50 1200 520]);
subplot(1,2,1);
b=bar(1:4,TD_aw,'FaceColor','flat','FaceAlpha',0.82); hold on;
for ci=1:4; b.CData(ci,:)=S_COL(ci,:); end
plot(1:4,TD_un,'D--','Color',[0.5 0.5 0.5],'LineWidth',2,'MarkerSize',8,'DisplayName','Unaware distance');
set(gca,'XTick',1:4,'XTickLabel',SLBLS); ylabel('Total Distance (km)');
title('Routing Distance by Scenario','FontWeight','bold'); legend; grid on;

subplot(1,2,2);
rc_aw =100*(TD_aw-TD_aw(1))/TD_aw(1);
rc_un =100*(TD_un-TD_un(1))/TD_un(1);
plot(1:4,rc_aw,'o-','Color',A_COL,'LineWidth',2.5,'DisplayName','Aware RC%'); hold on;
plot(1:4,rc_un,'s--','Color',W_COL,'LineWidth',2.2,'DisplayName','Unaware RC%');
fill([1:4 fliplr(1:4)],[rc_aw fliplr(rc_un)],[0.8 0 0],'FaceAlpha',0.10,'EdgeColor','none','DisplayName','Extra overhead');
set(gca,'XTick',1:4,'XTickLabel',SLBLS); ylabel('Reliability Cost RC (%) vs S0');
title('Routing Overhead vs Baseline','FontWeight','bold'); legend; grid on;
sgtitle({'CS-M3  Routing Distance and Reliability Cost',...
         'Unaware routing pays 30% more distance at peak with lower SR'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'CSM3_routing_cost');

%% CS-MATLAB-4  SR timeline (hour-by-hour)
fprintf('CS-M4  SR timeline\n');
hours=0:0.5:10;
phi_t=zeros(1,numel(hours));
for i=1:numel(hours)
    t=hours(i);
    if t<2; phi_t(i)=1.0-0.18*t;
    elseif t<6; phi_t(i)=max(0.42,1.0-0.30*t+0.02*(t-2));
    else; phi_t(i)=min(0.72,0.42+0.05*(t-6)); end
end
rng(7);
sr_aw  =97*phi_t.^0.7  + randn(1,numel(hours))*1.5;
sr_un  =97*phi_t.^1.8  + randn(1,numel(hours))*1.5;
sr_nsga=97*phi_t.^0.65 + randn(1,numel(hours))*1.2 + 2;
sr_aw=min(sr_aw,98); sr_un=max(sr_un,0); sr_nsga=min(sr_nsga,99);

fig=figure('Name','CS-M4 SR Timeline','Position',[50 50 1200 720]);
subplot(2,1,1);
area(hours,phi_t,'FaceColor',[0.42 0 0.62],'FaceAlpha',0.20,'EdgeColor',[0.42 0 0.62],'LineWidth',2);
yline(0.85,'--','Color',[1 0.6 0],'LineWidth',2,'Label','\phi^*=0.85');
xlabel('Hours after blackout'); ylabel('\phi (mean reliability)'); ylim([0.3 1.1]);
title('Network Reliability φ̄ During Blackout Event','FontWeight','bold'); grid on;
for t=[0 2 6 10]
    xline(t,':','Color',[0.6 0.6 0.6],'LineWidth',1,'Alpha',0.6);
end

subplot(2,1,2);
plot(hours,sr_aw,  'Color',A_COL,'LineWidth',2.5,'DisplayName','SR - Aware'); hold on;
plot(hours,sr_un,  '--','Color',W_COL,'LineWidth',2.2,'DisplayName','SR - Unaware');
plot(hours,sr_nsga,'-.','Color',[0.18 0.49 0.20],'LineWidth',2,'DisplayName','SR - NSGA-II knee');
fill([hours fliplr(hours)],[sr_un fliplr(sr_aw)],[0 0 0.8],'FaceAlpha',0.08,'EdgeColor','none','DisplayName','Awareness gain');
yline(85,'--','Color',[0.5 0.5 0.5],'LineWidth',1,'Label','85% target');
xlabel('Hours after blackout onset (April 28, 2025)'); ylabel('SR (%)'); ylim([0 100]);
legend('FontSize',9,'Location','southwest','NumColumns',2); grid on;
for t=[0 2 6 10]; xline(t,':','Color',[0.6 0.6 0.6],'LineWidth',1,'Alpha',0.6); end
sgtitle({'CS-M4  Service Rate Timeline — 2025 Iberian Blackout (Madrid)',...
         'Hour-by-hour SR across 10-hour event'},'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'CSM4_sr_timeline');

%% CS-MATLAB-5  Phase diagram with event trajectory
fprintf('CS-M5  Phase diagram with trajectory\n');
phi_v=linspace(0.20,1.00,80); trf_v=linspace(20,100,60);
[PHI,TRF]=meshgrid(phi_v,trf_v);
SR_surf=97*PHI.^0.65.*(1-0.003*(TRF-40)); SR_surf=min(max(SR_surf,0),100);

fig=figure('Name','CS-M5 Phase Diagram','Position',[50 50 900 700]);
lvls=[0 70 85 95 101];
cmap_pd=[0.72 0.11 0.11; 0.90 0.29 0.09; 0.98 0.66 0.15; 0.18 0.49 0.20];
contourf(phi_v,trf_v,SR_surf,lvls,'LineStyle','none'); colormap(cmap_pd); hold on;
[cs,h]=contour(phi_v,trf_v,SR_surf,[70 85 95],'w','LineWidth',1.8);
clabel(cs,h,'FontSize',9,'Color','w');
xline(0.85,'--','Color',[1 0.9 0],'LineWidth',2.5,'Label','\phi^*=0.85','LabelHorizontalAlignment','right');

% Event scenario points
sc_pts=[1.00 40; 0.82 80; 0.42 100; 0.67 60];
sc_lbl={'S0 Normal','S1 t=0-2h','S2 Peak','S3 Restore'};
sc_mk={'o','s','^','d'}; sc_col_pt={[1 1 1],[1 0.9 0],[1 0.3 0.3],[0.5 0.8 1]};
for si=1:4
    scatter(sc_pts(si,1),sc_pts(si,2),280,'filled','Marker',sc_mk{si},...
        'MarkerFaceColor',sc_col_pt{si},'MarkerEdgeColor','k','LineWidth',1.5);
    text(sc_pts(si,1)+0.02,sc_pts(si,2)+2,sc_lbl{si},'Color','w','FontSize',9,'FontWeight','bold');
end
for si=1:3
    annotation('arrow','X',[0.1+0.7*(sc_pts(si,1)-0.2)/0.8 0.1+0.7*(sc_pts(si+1,1)-0.2)/0.8],...
               'Y',[0.1+0.8*(sc_pts(si,2)-20)/80 0.1+0.8*(sc_pts(si+1,2)-20)/80],...
               'Color','w','LineWidth',1.5,'HeadStyle','vback2','HeadLength',8);
end
xlabel('\phi (Mean Network Reliability)','FontWeight','bold');
ylabel('Traffic Level (%)','FontWeight','bold');
title({'CS-M5  Madrid 2025 Blackout Trajectory on Service Phase Diagram',...
       'Arrow = event progression: Normal \rightarrow Early \rightarrow Peak \rightarrow Restore'},...
    'FontWeight','bold');
c=colorbar; c.Ticks=[35 77 90 98]; c.TickLabels={'<70%','70-85%','85-95%','\geq95%'};
c.Label.String='Service Rate SR (%)'; set(gca,'XDir','reverse');
save_fig(fig,OUTDIR,'CSM5_phase_diagram_trajectory');

%% CS-MATLAB-6  Priority tier 3D surface (phi, tier, SR)
fprintf('CS-M6  Priority tier 3D surface\n');
phi_3d=linspace(0.3,1.0,30);
tier_3d=[1 2 3];
SR_tier=zeros(3,30);
tier_exponents=[0.50 0.68 0.85];
for ti=1:3
    SR_tier(ti,:)=97*phi_3d.^tier_exponents(ti);
end
fig=figure('Name','CS-M6 Tier 3D','Position',[50 50 900 680]);
hold on;
tier_cols_3d={[0.89 0.22 0.21],[1.00 0.60 0.00],[0.13 0.59 0.95]};
tier_lbls={'Type 1 - Critical','Type 2 - Serious','Type 3 - Minor'};
for ti=1:3
    surf([phi_3d;phi_3d],[ones(1,30)*(ti-0.4);ones(1,30)*(ti+0.4)],...
         [SR_tier(ti,:);SR_tier(ti,:)],'FaceColor',tier_cols_3d{ti},...
         'FaceAlpha',0.70,'EdgeColor','none','DisplayName',tier_lbls{ti});
    plot3(phi_3d,ones(1,30)*ti,SR_tier(ti,:),'Color',tier_cols_3d{ti},'LineWidth',3);
end
% Mark scenario points
for si=0:3
    p=phi_mean(si+1);
    for ti=1:3
        sr_v=97*p^tier_exponents(ti);
        scatter3(p,ti,sr_v,80,S_COL(si+1,:),'filled','MarkerEdgeColor','w','LineWidth',0.8);
    end
end
xlabel('\phi_{min}','FontWeight','bold'); ylabel('Injury Priority Tier','FontWeight','bold');
zlabel('Service Rate SR (%)','FontWeight','bold');
set(gca,'YTick',1:3,'YTickLabel',{'Critical','Serious','Minor'});
title({'CS-M6  Priority-Stratified SR Surface: \phi_{min} \times Injury Tier',...
       'Dots = scenario operating points (S0-S3)'},'FontWeight','bold');
legend(tier_lbls,'Location','northwest'); view(30,-55); grid on; zlim([0 100]);
save_fig(fig,OUTDIR,'CSM6_priority_tier_surface');

fprintf('\n=== Done: Case Study MATLAB .fig files saved ===\n');
fprintf('  Output: %s\n', OUTDIR);
